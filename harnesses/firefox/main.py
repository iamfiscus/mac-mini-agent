"""Firefox harness — deterministic browser control via Marionette.

Faster and more reliable than steer for Firefox-specific tasks.
Requires Firefox started with: firefox --marionette

Usage:
    firefox navigate <url>
    firefox tabs [list|switch <index>|close <index>]
    firefox screenshot [--output path]
    firefox content [--format text|html]
"""

import click

from commands import navigate, tabs, screenshot, content


@click.group()
@click.option("--host", default="127.0.0.1", help="Marionette host")
@click.option("--port", default=2828, type=int, help="Marionette port")
@click.pass_context
def cli(ctx, host, port):
    """Firefox browser harness via Marionette protocol."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port


cli.add_command(navigate.navigate)
cli.add_command(tabs.tabs)
cli.add_command(screenshot.screenshot)
cli.add_command(content.content)


if __name__ == "__main__":
    cli()
