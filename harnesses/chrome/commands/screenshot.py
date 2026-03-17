"""Take a page screenshot via CDP."""

import asyncio
import base64
import json
import os
import uuid

import click

from connection import connect

SCREENSHOT_DIR = "/tmp/harness/chrome"


async def _screenshot(host, port, full_page):
    async with connect(host, port) as cdp:
        params = {"format": "png"}
        if full_page:
            # Get full page dimensions
            layout = await cdp.send("Page.getLayoutMetrics")
            content_size = layout.get("contentSize", layout.get("cssContentSize", {}))
            params["clip"] = {
                "x": 0, "y": 0,
                "width": content_size.get("width", 1920),
                "height": content_size.get("height", 1080),
                "scale": 1,
            }
        result = await cdp.send("Page.captureScreenshot", params)
        info = await cdp.send("Runtime.evaluate", {
            "expression": "JSON.stringify({url: location.href, title: document.title})"
        })
        page_info = json.loads(info["result"]["value"])
        return result["data"], page_info


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

    b64_data, page_info = asyncio.run(_screenshot(host, port, full_page))
    img_bytes = base64.b64decode(b64_data)
    with open(output, "wb") as f:
        f.write(img_bytes)

    if json_output:
        click.echo(json.dumps({
            "status": "ok",
            "screenshot": output,
            "title": page_info["title"],
            "url": page_info["url"],
            "size_bytes": len(img_bytes),
        }))
    else:
        click.echo(f"Screenshot saved: {output} ({len(img_bytes)} bytes)")
