"""X11 environment setup for Linux.

Call ensure_display() before any command that touches the X11 display
(xdotool, scrot, tesseract on screenshots, etc.). On macOS this is a no-op.
"""

import os
import platform
import subprocess


def ensure_display() -> None:
    """Set DISPLAY and XAUTHORITY env vars for X11 access from headless contexts (SSH, systemd)."""
    if platform.system() != "Linux":
        return

    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = _detect_display()

    if "XAUTHORITY" not in os.environ:
        xauth = f"/run/user/{os.getuid()}/gdm/Xauthority"
        if os.path.exists(xauth):
            os.environ["XAUTHORITY"] = xauth


def _detect_display() -> str:
    """Auto-detect the active X11 DISPLAY from the running GNOME session."""
    try:
        result = subprocess.run(
            [
                "bash", "-c",
                "cat /proc/$(pgrep -u $USER gnome-session | head -1)/environ 2>/dev/null"
                " | tr '\\0' '\\n' | grep ^DISPLAY=",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("=", 1)[1]
    except Exception:
        pass
    return ":1"
