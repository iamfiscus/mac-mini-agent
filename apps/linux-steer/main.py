"""linux-steer — X11 GUI automation CLI for AI agents.

Drop-in Linux replacement for macOS steer. Same commands, same JSON output,
different backend (xdotool + scrot + tesseract instead of Swift + Accessibility API).
"""

import click

from commands.see import see
from commands.click import click_cmd
from commands.type_cmd import type_cmd
from commands.hotkey import hotkey
from commands.ocr import ocr
from commands.apps import apps
from commands.focus import focus


@click.group()
@click.version_option(version="0.1.0", prog_name="steer (linux)")
def cli():
    """Linux X11 GUI automation CLI for AI agents. Eyes and hands on your desktop."""
    pass


cli.add_command(see)
cli.add_command(click_cmd, name="click")
cli.add_command(type_cmd, name="type")
cli.add_command(hotkey)
cli.add_command(ocr)
cli.add_command(apps)
cli.add_command(focus)


if __name__ == "__main__":
    cli()
