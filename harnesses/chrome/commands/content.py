"""Extract page content from DOM via CDP — faster and more accurate than OCR."""

import asyncio
import json

import click

from connection import connect


async def _content(host, port, fmt, selector):
    async with connect(host, port) as cdp:
        if selector:
            if fmt == "html":
                expr = f"document.querySelector('{selector}')?.outerHTML || ''"
            else:
                expr = f"document.querySelector('{selector}')?.innerText || ''"
        else:
            if fmt == "html":
                expr = "document.documentElement.outerHTML"
            else:
                expr = "document.body.innerText"

        result = await cdp.send("Runtime.evaluate", {"expression": expr})
        text = result["result"].get("value", "")

        info = await cdp.send("Runtime.evaluate", {
            "expression": "JSON.stringify({url: location.href, title: document.title})"
        })
        page_info = json.loads(info["result"]["value"])
        return text, page_info


@click.command()
@click.option("--format", "fmt", type=click.Choice(["text", "html"]), default="text")
@click.option("--selector", "-s", default=None, help="CSS selector to extract from")
@click.option("--json-output", "--json", is_flag=True)
@click.pass_context
def content(ctx, fmt, selector, json_output):
    """Extract page text or HTML content from the DOM."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    text, page_info = asyncio.run(_content(host, port, fmt, selector))

    if json_output:
        click.echo(json.dumps({
            "status": "ok",
            "title": page_info["title"],
            "url": page_info["url"],
            "format": fmt,
            "content": text,
            "length": len(text),
        }))
    else:
        click.echo(text)
