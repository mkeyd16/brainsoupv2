import os
import sys
import subprocess
import urllib.request
import time
import importlib
from pathlib import Path
import config

SUPPORTED_PYTHON_MIN = (3, 10)
SUPPORTED_PYTHON_MAX = (3, 13)

def check_python(sys_version_info=None) -> bool:
    version_info = sys_version_info or sys.version_info
    ver_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    if version_info < SUPPORTED_PYTHON_MIN or version_info >= SUPPORTED_PYTHON_MAX:
        print("==================================================")
        print(f"ERROR: Unsupported Python version detected: {ver_str}")
        print("wrld.v2 requires Python 3.10, 3.11, or 3.12 for prebuilt llama-cpp-python wheels.")
        print(f"Python {ver_str} lacks prebuilt binary wheels for llama-cpp-python, requiring C++/CMake build toolchains (NMake/MSVC).")
        print("Please install Python 3.10, 3.11, or 3.12 to enable 1-click startup without C++ compilers.")
        print("==================================================")
        return False

    print(f"Python version: {ver_str} - OK")
    return True

def find_supported_python_executable() -> str:
    """
    Scans for an installed supported Python interpreter (3.10, 3.11, or 3.12).
    Returns path or command string, or None if not found.
    """
    if check_python():
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
        try:
            res = subprocess.run(
                cmd + ["-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}'); sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0:
                return " ".join(cmd) if isinstance(cmd, list) else cmd
        except (subprocess.SubprocessError, FileNotFoundError):
            continue

    return None

def ensure_venv() -> str:
    """
    Ensures a project-local .venv directory exists and is created using a supported Python interpreter.
    Returns path to python executable inside .venv.
    """
    venv_dir = config.BASE_DIR / ".venv"
    if sys.platform == "win32":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    if venv_python.exists():
        try:
            res = subprocess.run(
                [str(venv_python), "-c", "import sys; sys.exit(0 if (3, 10) <= sys.version_info < (3, 13) else 1)"],
                capture_output=True,
                timeout=5
            )
            if res.returncode == 0:
                return str(venv_python)
        except Exception:
            pass

    # .venv missing or invalid - find supported Python to build .venv
    supported_exec = find_supported_python_executable()
    if not supported_exec:
        return None

    print(f"Creating local virtual environment in {venv_dir}...")
    cmd = supported_exec.split() + ["-m", "venv", str(venv_dir)]
    subprocess.check_call(cmd)
    return str(venv_python)

def check_dependencies(python_exec: str = None) -> bool:
    print("Checking Python dependencies...")
    target_python = python_exec or sys.executable

    missing = []
    try:
        importlib.import_module("llama_cpp")
    except ImportError:
        missing.append("llama-cpp-python")

    try:
        importlib.import_module("requests")
    except ImportError:
        missing.append("requests")

    if missing:
        print(f"Missing packages detected: {missing}")
        print("Installing required packages from requirements.txt...")
        cmd = [target_python, "-m", "pip", "install", "-r", str(config.BASE_DIR / "requirements.txt")]
        try:
            subprocess.check_call(cmd)
            print("Pip install command executed successfully.")
        except subprocess.CalledProcessError as e:
            print("==================================================")
            print(f"ERROR: Failed to install required Python dependencies (exit code {e.returncode}).")
            print("Ensure you are running a supported Python version (3.10-3.12) with internet access.")
            print("==================================================")
            return False

        try:
            importlib.import_module("llama_cpp")
            print("Post-install verification: llama_cpp imported successfully - OK")
        except ImportError:
            print("==================================================")
            print("ERROR: Post-install import verification failed for 'llama_cpp'.")
            print("Package installation appeared to complete, but llama_cpp is not importable.")
            print("==================================================")
            return False
    else:
        print("Dependencies: OK")

    return True

def download_file_with_resume(url: str, dest_path: Path, min_size: int) -> bool:
    dest_path = Path(dest_path)
    part_path = dest_path.with_suffix(".part")

    if dest_path.exists():
        if dest_path.stat().st_size >= min_size:
            print(f"File found: {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.1f} MB) - OK")
            return True
        else:
            print(f"Existing file {dest_path.name} is corrupted/too small ({dest_path.stat().st_size} bytes). Removing.")
            dest_path.unlink()

    print(f"Downloading model from {url}...")
    print(f"Saving temporary file to: {part_path.name}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    downloaded_bytes = 0
    if part_path.exists():
        downloaded_bytes = part_path.stat().st_size
        if downloaded_bytes >= min_size:
            part_path.rename(dest_path)
            print(f"Part file was complete. Promoted to {dest_path.name}")
            return True
        headers["Range"] = f"bytes={downloaded_bytes}-"
        print(f"Resuming download from byte {downloaded_bytes}...")

    mode = "ab" if "Range" in headers else "wb"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = getattr(response, "status", 200)

            if "Range" in headers and status_code == 200:
                print("Server does not support range requests. Restarting download...")
                downloaded_bytes = 0
                mode = "wb"

            content_length_header = response.headers.get("Content-Length")
            content_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else None
            total_size = (downloaded_bytes + content_length) if content_length else None

            block_size = 1024 * 1024
            last_report_bytes = downloaded_bytes
            last_report_time = time.time()

            print(f"Download started. Total size: {f'{total_size / (1024*1024):.1f} MB' if total_size else 'Unknown'}")

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

            print(f"Download finished: {downloaded_bytes / (1024*1024):.1f} MB received.")

    except Exception as e:
        print(f"Download error encountered: {e}")

    if part_path.exists():
        actual_size = part_path.stat().st_size
        if actual_size >= min_size:
            part_path.rename(dest_path)
            print(f"Verification successful. Saved to {dest_path.name}")
            return True
        else:
            print(f"Error: Downloaded file size ({actual_size} bytes) is less than expected minimum ({min_size} bytes).")
            return False
    else:
        print("Error: Temporary file .part does not exist after download attempt.")
        return False

def verify_and_setup_environment() -> bool:
    print("==================================================")
    print("Checking wrld.v2 installation...")
    print("==================================================")

    if not check_python():
        return False

    if not check_dependencies():
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
