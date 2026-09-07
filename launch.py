import os
import sys
import subprocess
import urllib.request
import time
from pathlib import Path
import config

def check_python():
    print(f"Python version: {sys.version.split()[0]} - OK")
    return True

def check_dependencies():
    print("Checking Python dependencies...")
    missing = []
    try:
        import llama_cpp
    except ImportError:
        missing.append("llama-cpp-python")

    try:
        import requests
    except ImportError:
        missing.append("requests")

    if missing:
        print(f"Missing packages detected: {missing}")
        print("Installing required packages...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(config.BASE_DIR / "requirements.txt")]
        subprocess.check_call(cmd)
        print("Dependencies installed successfully.")
    else:
        print("Dependencies: OK")
    return True

def download_file_with_resume(url: str, dest_path: Path, min_size: int) -> bool:
    """
    Downloads file using .part temporary path and resume support if possible.
    Outputs progress with automation-friendly newline-terminated messages.
    """
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
        # If part file is already bigger than expected or equal to target size, check if valid
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

            # If Range request wasn't supported (200 returned instead of 206), reset download
            if "Range" in headers and status_code == 200:
                print("Server does not support range requests. Restarting download...")
                downloaded_bytes = 0
                mode = "wb"

            content_length_header = response.headers.get("Content-Length")
            content_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else None
            total_size = (downloaded_bytes + content_length) if content_length else None

            block_size = 1024 * 1024  # 1MB blocks
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

                    # Periodically output status on a new line (every 50MB or every 5 seconds)
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

    # Final verification
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

def verify_and_setup_environment():
    print("==================================================")
    print("Checking wrld.v2 installation...")
    print("==================================================")

    check_python()
    check_dependencies()

    model_success = download_file_with_resume(
        url=config.MODEL_URL,
        dest_path=config.MODEL_PATH,
        min_size=config.MIN_MODEL_SIZE_BYTES
    )

    if not model_success:
        print("ERROR: Could not verify or download the AI model file.")
        sys.exit(1)

    print("Checking AI runtime... OK")
    print("Startup verification completed successfully!\n")
    return True

if __name__ == "__main__":
    verify_and_setup_environment()
