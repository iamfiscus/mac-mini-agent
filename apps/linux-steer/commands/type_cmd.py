"""Type — type text into the focused element."""

import subprocess

import click

from modules.display import ensure_display
from modules.output import emit


@click.command("type")
@click.argument("text")
@click.option("--into", default=None, help="Element ID to click first (from prior snapshot).")
@click.option("--delay", default=12, type=int, help="Delay between keystrokes in ms.")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def type_cmd(text, into, delay, as_json):
    """Type text into the currently focused element."""
    ensure_display()

    if into:
        # Agent should provide coordinates from prior see/ocr
        click.echo(f"Note: --into requires coordinates. Click the target element first.", err=True)

    subprocess.run(
        ["xdotool", "type", "--delay", str(delay), "--clearmodifiers", text],
        capture_output=True, text=True, timeout=30,
    )

    data = {"ok": True, "action": "type", "text": text}
    emit(data, as_json=as_json, human_lines=f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
