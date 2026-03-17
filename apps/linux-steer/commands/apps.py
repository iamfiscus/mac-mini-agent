"""Apps — list running applications and activate them."""

import subprocess

import click

from modules.display import ensure_display
from modules.output import emit


def _list_apps() -> list[dict]:
    """List running GUI applications via wmctrl."""
    ensure_display()
    result = subprocess.run(
        ["wmctrl", "-l", "-p"],
        capture_output=True, text=True, timeout=5,
    )
    apps = []
    seen_names = set()
    for line in result.stdout.strip().splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 5:
            wid = parts[0]
            name = parts[4]
            if name and name not in seen_names:
                seen_names.add(name)
                apps.append({"window_id": wid, "name": name})
    return apps


@click.command()
@click.argument("action", default="list", type=click.Choice(["list", "activate"]))
@click.argument("name", default="", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def apps(action, name, as_json):
    """List running applications or activate one by name."""
    ensure_display()

    if action == "list":
        app_list = _list_apps()
        data = {"ok": True, "apps": app_list, "count": len(app_list)}
        human = "\n".join(f"  {a['name']}" for a in app_list)
        emit(data, as_json=as_json, human_lines=f"Running apps ({len(app_list)}):\n{human}")

    elif action == "activate":
        if not name:
            click.echo("Error: provide app name to activate", err=True)
            raise SystemExit(1)
        search = subprocess.run(
            ["xdotool", "search", "--limit", "1", "--name", name],
            capture_output=True, text=True, timeout=5,
        )
        if search.returncode == 0 and search.stdout.strip():
            wid = search.stdout.strip().splitlines()[0]
            subprocess.run(["xdotool", "windowactivate", wid], capture_output=True, text=True, timeout=5)
            ok = True
        else:
            ok = False
        data = {"ok": ok, "action": "activate", "app": name}
        emit(data, as_json=as_json, human_lines=f"{'Activated' if ok else 'Failed to activate'}: {name}")
