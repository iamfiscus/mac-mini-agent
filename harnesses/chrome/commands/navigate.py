"""Navigate to a URL via CDP."""

import asyncio
import json
import time

import click

from connection import connect


async def _navigate(host, port, url, wait):
    start = time.time()
    async with connect(host, port) as cdp:
        await cdp.send("Page.enable")
        await cdp.send("Page.navigate", {"url": url})
        if wait > 0:
            await asyncio.sleep(wait)
        # Get current URL and title
        result = await cdp.send("Runtime.evaluate", {
            "expression": "JSON.stringify({url: location.href, title: document.title})"
        })
        info = json.loads(result["result"]["value"])
        elapsed = time.time() - start
        return {**info, "elapsed_ms": int(elapsed * 1000)}


@click.command()
@click.argument("url")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@click.option("--wait", default=1.0, type=float, help="Seconds to wait after navigation")
@click.pass_context
def navigate(ctx, url, json_output, wait):
    """Navigate Chrome to a URL."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    if not url.startswith(("http://", "https://", "about:", "file://", "chrome://")):
        url = "https://" + url

    result = asyncio.run(_navigate(host, port, url, wait))

    if json_output:
        click.echo(json.dumps({"status": "ok", **result}))
    else:
        click.echo(f"Navigated to: {result['url']}")
        click.echo(f"Title: {result['title']}")
        click.echo(f"Elapsed: {result['elapsed_ms']}ms")
