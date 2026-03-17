"""Focus — show or set the currently focused element/window."""

import subprocess

import click

from modules.display import ensure_display
from modules.output import emit


@click.command()
@click.argument("app", default="", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def focus(app, as_json):
    """Show the currently focused window, or activate an app by name."""
    ensure_display()

    if app:
        # Find the first matching window, then activate it separately
        search = subprocess.run(
            ["xdotool", "search", "--limit", "1", "--name", app],
            capture_output=True, text=True, timeout=5,
        )
        if search.returncode == 0 and search.stdout.strip():
            wid = search.stdout.strip().splitlines()[0]
            subprocess.run(
                ["xdotool", "windowactivate", wid],
                capture_output=True, text=True, timeout=5,
            )
            ok = True
        else:
            ok = False
        data = {"ok": ok, "action": "focus", "app": app}
        emit(data, as_json=as_json, human_lines=f"{'Focused' if ok else 'Failed to focus'}: {app}")
    else:
        # Get active window info
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True, text=True, timeout=5,
        )
        name = result.stdout.strip() if result.returncode == 0 else "unknown"

        wid_result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=5,
        )
        wid = wid_result.stdout.strip() if wid_result.returncode == 0 else ""

        data = {"ok": True, "focused_window": name, "window_id": wid}
        emit(data, as_json=as_json, human_lines=f"Focused: {name}")
