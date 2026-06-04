"""Capture a single still frame, for the camera bringup test.

Tries picamera2 first (the modern Pi camera stack), then falls back to the
rpicam-still CLI. Returns (ok, backend_or_error).
"""
from __future__ import annotations

import os
import subprocess
import time

# Quiet libcamera's INFO chatter so the bringup output stays readable.
os.environ.setdefault("LIBCAMERA_LOG_LEVELS", "*:ERROR")

DEFAULT_PATH = "/tmp/growbot_frame.jpg"


def capture(path: str = DEFAULT_PATH, width: int = 640, height: int = 480) -> tuple[bool, str]:
    pic_err = ""
    try:
        from picamera2 import Picamera2

        cam = Picamera2()
        cam.configure(cam.create_still_configuration(main={"size": (width, height)}))
        cam.start()
        time.sleep(0.4)
        cam.capture_file(path)
        cam.stop()
        cam.close()
        return True, "picamera2"
    except Exception as exc:
        pic_err = f"{type(exc).__name__}: {exc}"

    try:
        subprocess.run(
            ["rpicam-still", "-n", "--width", str(width), "--height", str(height), "-o", path, "--timeout", "500"],
            check=True,
            capture_output=True,
            timeout=12,
        )
        return True, "rpicam-still"
    except Exception as exc:
        return False, f"picamera2 failed ({pic_err}); rpicam-still failed ({exc})"
