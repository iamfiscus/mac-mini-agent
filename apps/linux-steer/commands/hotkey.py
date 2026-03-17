"""Hotkey — send keyboard shortcuts."""

import subprocess

import click

from modules.display import ensure_display
from modules.output import emit

# Map common macOS-style names to xdotool key names
KEY_MAP = {
    "cmd": "super",
    "command": "super",
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "option": "alt",
    "shift": "shift",
    "return": "Return",
    "enter": "Return",
    "escape": "Escape",
    "esc": "Escape",
    "tab": "Tab",
    "space": "space",
    "delete": "Delete",
    "backspace": "BackSpace",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
}


def _normalize_key(key: str) -> str:
    return KEY_MAP.get(key.lower(), key)


@click.command()
@click.argument("keys")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def hotkey(keys, as_json):
    """Send a keyboard shortcut (e.g., 'ctrl+s', 'alt+tab', 'return').

    Use '+' to combine modifiers: ctrl+shift+t, super+l, etc.
    """
    ensure_display()

    parts = [_normalize_key(k.strip()) for k in keys.split("+")]
    xdotool_key = "+".join(parts)

    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", xdotool_key],
        capture_output=True, text=True, timeout=5,
    )

    data = {"ok": True, "action": "hotkey", "keys": keys, "xdotool_key": xdotool_key}
    emit(data, as_json=as_json, human_lines=f"Sent: {keys}")
