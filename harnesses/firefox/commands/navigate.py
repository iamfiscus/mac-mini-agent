"""Navigate to a URL."""

import json
import time

import click

from connection import connect


@click.command()
@click.argument("url")
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@click.option("--wait", default=1.0, type=float, help="Seconds to wait after navigation")
@click.pass_context
def navigate(ctx, url, json_output, wait):
    """Navigate Firefox to a URL."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    # Add scheme if missing
    if not url.startswith(("http://", "https://", "about:", "file://")):
        url = "https://" + url

    start = time.time()
    with connect(host, port) as client:
        client.navigate(url)
        if wait > 0:
            time.sleep(wait)
        current_url = client.get_url()
        title = client.title
        elapsed = time.time() - start

    if json_output:
        click.echo(json.dumps({
            "status": "ok",
            "url": current_url,
            "title": title,
            "elapsed_ms": int(elapsed * 1000),
        }))
    else:
        click.echo(f"Navigated to: {current_url}")
        click.echo(f"Title: {title}")
        click.echo(f"Elapsed: {elapsed:.1f}s")
