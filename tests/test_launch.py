import unittest
import tempfile
import urllib.error
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from launch import (
    download_file_with_resume,
    check_python_version,
    find_supported_python_executable,
    bootstrap_official_python,
    ensure_venv,
    check_dependencies,
    verify_and_setup_environment
)

class DummyHeader:
    def __init__(self, headers_dict):
        self.headers_dict = headers_dict

    def get(self, key, default=None):
        for k, v in self.headers_dict.items():
            if k.lower() == key.lower():
                return v
        return default

class DummyResponse:
    def __init__(self, data_blocks, headers_dict=None, status=200):
        self.data_blocks = list(data_blocks)
        self.headers = DummyHeader(headers_dict or {})
        self.status = status

    def read(self, block_size):
        if self.data_blocks:
            return self.data_blocks.pop(0)
        return b""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyVersionInfo:
    def __init__(self, major, minor, micro):
        self.major = major
        self.minor = minor
        self.micro = micro

    def __lt__(self, other):
        return (self.major, self.minor) < other

    def __ge__(self, other):
        return (self.major, self.minor) >= other

class TestLaunchBootstrap(unittest.TestCase):

    def test_python_version_check_supported(self):
        v312 = DummyVersionInfo(3, 12, 0)
        self.assertTrue(check_python_version(v312))

        v311 = DummyVersionInfo(3, 11, 4)
        self.assertTrue(check_python_version(v311))

        v310 = DummyVersionInfo(3, 10, 5)
        self.assertTrue(check_python_version(v310))

    def test_python_version_check_unsupported(self):
        v314 = DummyVersionInfo(3, 14, 6)
        self.assertFalse(check_python_version(v314))

        v313 = DummyVersionInfo(3, 13, 0)
        self.assertFalse(check_python_version(v313))

        v39 = DummyVersionInfo(3, 9, 2)
        self.assertFalse(check_python_version(v39))

    @patch("launch.verify_python_executable")
    def test_find_supported_python_executable_prefers_py_launcher(self, mock_verify):
        mock_verify.side_effect = lambda cmd: "py -3.12" in str(cmd) or cmd == ["py", "-3.12"]

        v314 = DummyVersionInfo(3, 14, 6)
        with patch("sys.version_info", v314):
            exec_found = find_supported_python_executable()
            self.assertEqual(exec_found, "py -3.12")

    @patch("launch.PYTHON_RUNTIME_DIR", new_callable=lambda: Path("/nonexistent_runtime_dir"))
    @patch("launch.bootstrap_official_python")
    @patch("subprocess.run")
    def test_find_supported_python_executable_triggers_bootstrap_if_none_installed(self, mock_run, mock_bootstrap, mock_runtime_dir):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_run.return_value = mock_proc
        mock_bootstrap.return_value = "/app/runtime/python312/python.exe"

        v314 = DummyVersionInfo(3, 14, 6)
        with patch("sys.version_info", v314):
            exec_found = find_supported_python_executable()
            self.assertEqual(exec_found, "/app/runtime/python312/python.exe")
            mock_bootstrap.assert_called_once()

    @patch("subprocess.check_call")
    def test_check_dependencies_already_present(self, mock_check_call):
        with patch.dict("sys.modules", {"llama_cpp": MagicMock(), "requests": MagicMock(), "tkinter": MagicMock()}):
            result = check_dependencies()
            self.assertTrue(result)
            mock_check_call.assert_not_called()

    @patch("subprocess.check_call")
    def test_check_dependencies_missing_installation_success(self, mock_check_call):
        mock_check_call.return_value = 0
        fake_llama_cpp = MagicMock()

        def mock_import(name):
            if name == "llama_cpp":
                if mock_import.call_count == 0:
                    mock_import.call_count += 1
                    raise ImportError("No module named 'llama_cpp'")
                return fake_llama_cpp
            return MagicMock()

        mock_import.call_count = 0

        with patch("importlib.import_module", side_effect=mock_import):
            result = check_dependencies()
            self.assertTrue(result)
            mock_check_call.assert_called_once()

    @patch("subprocess.check_call")
    def test_check_dependencies_missing_installation_failure(self, mock_check_call):
        mock_check_call.side_effect = subprocess.CalledProcessError(1, ["pip", "install"])
        with patch("importlib.import_module", side_effect=ImportError("No module named 'llama_cpp'")):
            result = check_dependencies()
            self.assertFalse(result)

    def test_existing_valid_model_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            dest.write_bytes(b"A" * 100)
            result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
            self.assertTrue(result)

    def test_existing_corrupt_file_replaced(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            dest.write_bytes(b"A" * 10)

            data = b"X" * 60
            mock_resp = DummyResponse([data], {"Content-Length": "60"})

            import urllib.request
            original_urlopen = urllib.request.urlopen
            try:
                urllib.request.urlopen = lambda req, timeout=30: mock_resp
                result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
                self.assertTrue(result)
                self.assertTrue(dest.exists())
                self.assertEqual(dest.stat().st_size, 60)
            finally:
                urllib.request.urlopen = original_urlopen

    def test_unknown_content_length(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            data = b"B" * 80
            mock_resp = DummyResponse([data], {})

            import urllib.request
            original_urlopen = urllib.request.urlopen
            try:
                urllib.request.urlopen = lambda req, timeout=30: mock_resp
                result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
                self.assertTrue(result)
                self.assertEqual(dest.stat().st_size, 80)
            finally:
                urllib.request.urlopen = original_urlopen

    def test_existing_completed_part_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            part = dest.with_suffix(".part")
            part.write_bytes(b"C" * 100)

            result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
            self.assertTrue(result)
            self.assertTrue(dest.exists())
            self.assertFalse(part.exists())

    def test_network_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"

            import urllib.request
            def mock_raise(req, timeout=30):
                raise urllib.error.URLError("Connection refused")

            original_urlopen = urllib.request.urlopen
            try:
                urllib.request.urlopen = mock_raise
                result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
                self.assertFalse(result)
                self.assertFalse(dest.exists())
            finally:
                urllib.request.urlopen = original_urlopen

if __name__ == "__main__":
    unittest.main()
