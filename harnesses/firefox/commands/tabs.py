"""Tab management — list, switch, close."""

import json

import click

from connection import connect


@click.group()
@click.pass_context
def tabs(ctx):
    """Manage Firefox tabs."""
    pass


@tabs.command("list")
@click.option("--json-output", "--json", is_flag=True)
@click.pass_context
def list_tabs(ctx, json_output):
    """List all open tabs."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    with connect(host, port) as client:
        handles = client.window_handles
        current = client.current_window_handle
        tab_info = []
        for i, handle in enumerate(handles):
            client.switch_to_window(handle)
            tab_info.append({
                "index": i,
                "handle": handle,
                "title": client.title,
                "url": client.get_url(),
                "active": handle == current,
            })
        # Switch back to original
        client.switch_to_window(current)

    if json_output:
        click.echo(json.dumps(tab_info, indent=2))
    else:
        for tab in tab_info:
            marker = " *" if tab["active"] else ""
            click.echo(f"[{tab['index']}]{marker} {tab['title']} — {tab['url']}")


@tabs.command()
@click.argument("index", type=int)
@click.pass_context
def switch(ctx, index):
    """Switch to a tab by index."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    with connect(host, port) as client:
        handles = client.window_handles
        if index < 0 or index >= len(handles):
            click.echo(f"Error: tab index {index} out of range (0-{len(handles)-1})", err=True)
            raise SystemExit(1)
        client.switch_to_window(handles[index])
        click.echo(f"Switched to tab {index}: {client.title}")


@tabs.command()
@click.argument("index", type=int)
@click.pass_context
def close(ctx, index):
    """Close a tab by index."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    with connect(host, port) as client:
        handles = client.window_handles
        if index < 0 or index >= len(handles):
            click.echo(f"Error: tab index {index} out of range (0-{len(handles)-1})", err=True)
            raise SystemExit(1)
        client.switch_to_window(handles[index])
        title = client.title
        client.close()
        click.echo(f"Closed tab {index}: {title}")
