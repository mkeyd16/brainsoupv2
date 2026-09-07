import sys
import os
from pathlib import Path

# Ensure project root is in sys.path before importing local modules
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import subprocess
import urllib.request
import zipfile
import time
import importlib
import config

SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX = (3, 13)

OFFICIAL_PYTHON_ZIP_URL = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
PYTHON_RUNTIME_DIR = config.RUNTIME_DIR / "python312"
PREBUILT_LLAMA_CPP_WHEEL_URL = "https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.30/llama_cpp_python-0.3.30-py3-none-win_amd64.whl"

def check_python_version(sys_version_info=None) -> bool:
    version_info = sys_version_info or sys.version_info
    return SUPPORTED_PYTHON_MIN <= (version_info.major, version_info.minor) < SUPPORTED_PYTHON_MAX

def verify_python_executable(exec_cmd) -> bool:
    try:
        if isinstance(exec_cmd, (str, Path)):
            cmd = [str(exec_cmd)]
        else:
            cmd = [str(c) for c in exec_cmd]
        res = subprocess.run(
            cmd + ["-c", "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False

def download_file_with_resume(url: str, dest_path: Path, min_size: int = 0) -> bool:
    dest_path = Path(dest_path)
    part_path = dest_path.with_suffix(".part")

    if dest_path.exists():
        if min_size == 0 or dest_path.stat().st_size >= min_size:
            return True
        else:
            dest_path.unlink()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    downloaded_bytes = 0
    if part_path.exists():
        downloaded_bytes = part_path.stat().st_size
        headers["Range"] = f"bytes={downloaded_bytes}-"

    mode = "ab" if "Range" in headers else "wb"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = getattr(response, "status", 200)

            if "Range" in headers and status_code == 200:
                downloaded_bytes = 0
                mode = "wb"

            content_length_header = response.headers.get("Content-Length")
            content_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else None
            total_size = (downloaded_bytes + content_length) if content_length else None

            block_size = 1024 * 1024
            last_report_bytes = downloaded_bytes
            last_report_time = time.time()

            with open(part_path, mode) as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded_bytes += len(buffer)

                    now = time.time()
                    if (downloaded_bytes - last_report_bytes >= 50 * 1024 * 1024) or (now - last_report_time >= 5.0):
                        if total_size and total_size > 0:
                            percent = (downloaded_bytes / total_size) * 100
                            print(f"Downloaded {downloaded_bytes / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)")
                        else:
                            print(f"Downloaded {downloaded_bytes / (1024*1024):.1f} MB")
                        last_report_bytes = downloaded_bytes
                        last_report_time = now

    except Exception as e:
        print(f"Download error encountered for {url}: {e}")

    if part_path.exists():
        actual_size = part_path.stat().st_size
        if min_size == 0 or actual_size >= min_size:
            part_path.rename(dest_path)
            return True
        else:
            return False
    return False

def bootstrap_official_python() -> str:
    PYTHON_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    target_python = PYTHON_RUNTIME_DIR / ("python.exe" if sys.platform == "win32" else "python")

    if verify_python_executable(target_python):
        return str(target_python)

    print("No supported Python (3.10-3.12) found on host system.")
    print("Automatically downloading official Python 3.12.8 runtime from python.org...")

    zip_path = config.RUNTIME_DIR / "python-3.12.8-embed-amd64.zip"
    success = download_file_with_resume(OFFICIAL_PYTHON_ZIP_URL, zip_path, min_size=5 * 1024 * 1024)
    if not success:
        print("ERROR: Failed to download official Python 3.12 package from python.org.")
        return None

    print(f"Extracting official Python 3.12 runtime into {PYTHON_RUNTIME_DIR}...")
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(PYTHON_RUNTIME_DIR)

        pth_file = list(PYTHON_RUNTIME_DIR.glob("*._pth"))
        if pth_file:
            pth_path = pth_file[0]
            content = pth_path.read_text(encoding="utf-8")
            if "#import site" in content:
                content = content.replace("#import site", "import site")
                pth_path.write_text(content, encoding="utf-8")

        get_pip_path = config.RUNTIME_DIR / "get-pip.py"
        download_file_with_resume(GET_PIP_URL, get_pip_path)
        if get_pip_path.exists():
            subprocess.run([str(target_python), str(get_pip_path), "--no-warn-script-location"], capture_output=True, timeout=60)

    except Exception as e:
        print(f"ERROR: Failed to set up bootstrapped Python runtime: {e}")
        return None

    if verify_python_executable(target_python):
        print(f"Bootstrapped Python 3.12 successfully at {target_python}")
        return str(target_python)

    return None

def find_supported_python_executable() -> str:
    bootstrapped = PYTHON_RUNTIME_DIR / ("python.exe" if sys.platform == "win32" else "python")
    if verify_python_executable(bootstrapped):
        return str(bootstrapped)

    if check_python_version():
        return sys.executable

    candidates = [
        ["py", "-3.12"],
        ["py", "-3.11"],
        ["py", "-3.10"],
        ["python3.12"],
        ["python3.11"],
        ["python3.10"],
        ["python"]
    ]

    for cmd in candidates:
        if verify_python_executable(cmd):
            return " ".join(cmd) if isinstance(cmd, list) else cmd

    return bootstrap_official_python()

def ensure_venv() -> str:
    venv_dir = config.BASE_DIR / ".venv"
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        if verify_python_executable(venv_python):
            return str(venv_python)
        else:
            print("Existing .venv uses an unsupported Python version. Removing .venv...")
            import shutil
            try:
                shutil.rmtree(venv_dir)
            except Exception as e:
                print(f"Warning: Failed to delete invalid .venv: {e}")

    supported_exec = find_supported_python_executable()
    if not supported_exec:
        print("ERROR: Could not locate or bootstrap a supported Python 3.10-3.12 interpreter.")
        return None

    if str(PYTHON_RUNTIME_DIR) in str(supported_exec):
        return supported_exec

    print(f"Creating local virtual environment in {venv_dir} using {supported_exec}...")
    if isinstance(supported_exec, str):
        cmd = supported_exec.split() + ["-m", "venv", str(venv_dir)]
    else:
        cmd = [str(c) for c in supported_exec] + ["-m", "venv", str(venv_dir)]

    try:
        subprocess.check_call(cmd)
    except Exception:
        venv_dir.mkdir(parents=True, exist_ok=True)

    if verify_python_executable(venv_python):
        return str(venv_python)

    return supported_exec

def check_module_importable(target_python: str, module_name: str) -> bool:
    if target_python == sys.executable:
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    try:
        res = subprocess.run(
            [target_python, "-c", f"import {module_name}"],
            capture_output=True,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False

def check_dependencies(python_exec: str = None) -> bool:
    print("Checking Python dependencies...")
    target_python = python_exec or sys.executable

    missing = []
    if not check_module_importable(target_python, "llama_cpp"):
        missing.append("llama-cpp-python")

    if not check_module_importable(target_python, "requests"):
        missing.append("requests")

    if missing:
        print(f"Missing packages detected: {missing}")
        print("Installing required packages from requirements.txt...")

        cmd = [target_python, "-m", "pip", "install", "--no-warn-script-location", "--prefer-binary", "--only-binary=:all:", "-r", str(config.BASE_DIR / "requirements.txt")]

        if sys.platform == "win32" and "llama-cpp-python" in missing:
            cmd = [target_python, "-m", "pip", "install", "--no-warn-script-location", "--prefer-binary", PREBUILT_LLAMA_CPP_WHEEL_URL, "-r", str(config.BASE_DIR / "requirements.txt")]

        try:
            subprocess.check_call(cmd)
            print("Pip install command executed successfully.")
        except subprocess.CalledProcessError as e:
            print("==================================================")
            print(f"ERROR: Failed to install required Python dependencies (exit code {e.returncode}).")
            print("Ensure you are running a supported Python version (3.10-3.12) with internet access.")
            print("==================================================")
            return False

        if check_module_importable(target_python, "llama_cpp"):
            print("Post-install verification: llama_cpp imported successfully - OK")
        else:
            print("==================================================")
            print("ERROR: Post-install import verification failed for 'llama_cpp'.")
            print("Package installation appeared to complete, but llama_cpp is not importable.")
            print("==================================================")
            return False
    else:
        print("Dependencies: OK")

    return True

def verify_and_setup_environment() -> bool:
    print("==================================================")
    print("Checking wrld.v2 installation...")
    print("==================================================")

    target_python = sys.executable

    if not check_python_version():
        print(f"Current interpreter ({sys.version.split()[0]}) is unsupported.")
        target_python = ensure_venv()
        if not target_python or not verify_python_executable(target_python):
            print("ERROR: Could not establish a supported Python 3.10-3.12 environment.")
            return False

    if not check_dependencies(python_exec=target_python):
        return False

    model_success = download_file_with_resume(
        url=config.MODEL_URL,
        dest_path=config.MODEL_PATH,
        min_size=config.MIN_MODEL_SIZE_BYTES
    )

    if not model_success:
        print("ERROR: Could not verify or download the AI model file.")
        return False

    print("Checking AI runtime... OK")
    print("Startup verification completed successfully!\n")
    return True

if __name__ == "__main__":
    success = verify_and_setup_environment()
    if not success:
        sys.exit(1)
