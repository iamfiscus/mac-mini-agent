"""Tab management via CDP HTTP endpoint."""

import json

import click

from connection import list_targets


@click.group()
@click.pass_context
def tabs(ctx):
    """Manage Chrome tabs."""
    pass


@tabs.command("list")
@click.option("--json-output", "--json", is_flag=True)
@click.pass_context
def list_tabs(ctx, json_output):
    """List all open tabs."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    targets = list_targets(host, port)
    pages = [t for t in targets if t.get("type") == "page"]

    tab_info = [
        {
            "index": i,
            "title": p.get("title", ""),
            "url": p.get("url", ""),
            "id": p.get("id", ""),
        }
        for i, p in enumerate(pages)
    ]

    if json_output:
        click.echo(json.dumps(tab_info, indent=2))
    else:
        for tab in tab_info:
            click.echo(f"[{tab['index']}] {tab['title']} — {tab['url']}")


@tabs.command()
@click.argument("index", type=int)
@click.pass_context
def close(ctx, index):
    """Close a tab by index."""
    import httpx

    host = ctx.obj["host"]
    port = ctx.obj["port"]

    targets = list_targets(host, port)
    pages = [t for t in targets if t.get("type") == "page"]
    if index < 0 or index >= len(pages):
        click.echo(f"Error: tab index {index} out of range (0-{len(pages)-1})", err=True)
        raise SystemExit(1)

    tab_id = pages[index]["id"]
    title = pages[index].get("title", "")
    httpx.get(f"http://{host}:{port}/json/close/{tab_id}")
    click.echo(f"Closed tab {index}: {title}")
