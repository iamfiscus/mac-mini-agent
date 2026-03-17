"""Take a page screenshot."""

import base64
import json
import os
import uuid

import click

from connection import connect

SCREENSHOT_DIR = "/tmp/harness/firefox"


@click.command()
@click.option("--output", "-o", default=None, help="Output file path")
@click.option("--full-page", is_flag=True, help="Capture full scrollable page")
@click.option("--json-output", "--json", is_flag=True)
@click.pass_context
def screenshot(ctx, output, full_page, json_output):
    """Take a screenshot of the current page."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if output is None:
        output = os.path.join(SCREENSHOT_DIR, f"{uuid.uuid4().hex[:8]}.png")

    with connect(host, port) as client:
        # Marionette screenshot returns base64
        b64_data = client.screenshot(full=full_page)
        img_bytes = base64.b64decode(b64_data)
        with open(output, "wb") as f:
            f.write(img_bytes)
        title = client.title
        url = client.get_url()

    if json_output:
        click.echo(json.dumps({
            "status": "ok",
            "screenshot": output,
            "title": title,
            "url": url,
            "size_bytes": len(img_bytes),
        }))
    else:
        click.echo(f"Screenshot saved: {output} ({len(img_bytes)} bytes)")
