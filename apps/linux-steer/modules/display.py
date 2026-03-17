"""X11 display environment and screen info."""

import os
import subprocess
import sys

# Add parent for shared module access
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..", "shared")))


def ensure_display() -> None:
    """Ensure DISPLAY and XAUTHORITY are set for X11 access."""
    from x11 import ensure_display as _ensure
    _ensure()


def get_screen_size() -> tuple[int, int]:
    """Get primary screen resolution via xrandr."""
    ensure_display()
    result = subprocess.run(
        ["xrandr", "--query"],
        capture_output=True, text=True, timeout=5,
    )
    for line in result.stdout.splitlines():
        if " connected primary" in line or (" connected" in line and "primary" not in result.stdout):
            # Parse resolution from line like "HDMI-1 connected primary 1920x1080+0+0"
            for part in line.split():
                if "x" in part and "+" in part:
                    res = part.split("+")[0]
                    w, h = res.split("x")
                    return int(w), int(h)
    return 1920, 1080  # fallback
