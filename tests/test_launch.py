import unittest
import tempfile
import urllib.error
from pathlib import Path

from launch import download_file_with_resume

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

class TestDownloader(unittest.TestCase):

    def test_existing_valid_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            dest.write_bytes(b"A" * 100)
            result = download_file_with_resume("http://example.com/model.gguf", dest, min_size=50)
            self.assertTrue(result)

    def test_existing_corrupt_file_replaced(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "model.gguf"
            dest.write_bytes(b"A" * 10)  # Too small (< 50)

            # Mock urlopen
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
            mock_resp = DummyResponse([data], {})  # No Content-Length

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
