"""Chrome harness — deterministic browser control via DevTools Protocol.

Faster and more reliable than steer for Chrome-specific tasks.
Requires Chrome started with: google-chrome --remote-debugging-port=9222

Usage:
    chrome-harness navigate <url>
    chrome-harness tabs list
    chrome-harness screenshot [--output path]
    chrome-harness content [--format text|html]
"""

import click

from commands import navigate, tabs, screenshot, content


@click.group()
@click.option("--host", default="127.0.0.1", help="CDP host")
@click.option("--port", default=9222, type=int, help="CDP port")
@click.pass_context
def cli(ctx, host, port):
    """Chrome browser harness via DevTools Protocol."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port


cli.add_command(navigate.navigate)
cli.add_command(tabs.tabs)
cli.add_command(screenshot.screenshot)
cli.add_command(content.content)


if __name__ == "__main__":
    cli()
