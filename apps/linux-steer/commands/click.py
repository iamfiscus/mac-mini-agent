"""Click — click by coordinates, element ID, or text match."""

import subprocess

import click as clicklib

from modules.display import ensure_display
from modules.output import emit, emit_error


@clicklib.command("click")
@clicklib.option("--x", type=int, default=None, help="X coordinate.")
@clicklib.option("--y", type=int, default=None, help="Y coordinate.")
@clicklib.option("--text", default=None, help="Click on detected text (requires prior OCR --store).")
@clicklib.option("--id", "element_id", default=None, help="Element ID from last snapshot (B1, T1, O1, etc.).")
@clicklib.option("--button", type=int, default=1, help="Mouse button (1=left, 2=middle, 3=right).")
@clicklib.option("--json", "as_json", is_flag=True, help="Output JSON.")
def click_cmd(x, y, text, element_id, button, as_json):
    """Click at coordinates or on a detected element."""
    ensure_display()

    if x is not None and y is not None:
        _click_at(x, y, button)
        data = {"ok": True, "action": "click", "x": x, "y": y, "button": button}
        emit(data, as_json=as_json, human_lines=f"Clicked at ({x}, {y})")
    elif text:
        # Use xdotool to search for window text — best effort
        # In practice, agents should OCR first, then click by coordinates
        emit_error(
            "Text-based click requires prior 'steer ocr --store' and using --id or --x/--y from the result",
            as_json=as_json,
        )
    elif element_id:
        emit_error(
            "Element ID click requires the element store from a prior 'steer see' or 'steer ocr --store'. "
            "Use the x,y coordinates from that result with --x and --y.",
            as_json=as_json,
        )
    else:
        emit_error("Provide --x/--y, --text, or --id", as_json=as_json)


def _click_at(x: int, y: int, button: int = 1) -> None:
    subprocess.run(
        ["xdotool", "mousemove", "--sync", str(x), str(y)],
        capture_output=True, text=True, timeout=5,
    )
    subprocess.run(
        ["xdotool", "click", str(button)],
        capture_output=True, text=True, timeout=5,
    )
