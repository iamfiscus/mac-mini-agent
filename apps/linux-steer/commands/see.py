"""Capture screenshot and accessibility tree."""

import os
import subprocess
import uuid

import click

from modules.display import ensure_display
from modules.elements import ElementStore
from modules.output import emit, emit_error


def _screenshot(app: str | None = None, screen: int | None = None) -> str:
    """Take a screenshot with scrot, return the file path."""
    ensure_display()
    os.makedirs("/tmp/steer", exist_ok=True)
    path = f"/tmp/steer/{uuid.uuid4().hex[:8]}.png"

    cmd = ["scrot", path]
    if app:
        # Capture focused window only
        cmd = ["scrot", "-u", path]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return ""
    return path


def _get_accessibility_tree(app: str | None = None) -> list[dict]:
    """Walk AT-SPI2 tree via gdbus. Returns raw element dicts."""
    # AT-SPI2 introspection via python3-atspi or gdbus
    # This is a best-effort approach — works well for GTK/Qt apps
    try:
        script = """
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi
import json

def walk(obj, depth=0, results=None):
    if results is None:
        results = []
    if depth > 10:
        return results
    try:
        role = obj.get_role_name()
        name = obj.get_name() or ""
        try:
            comp = obj.get_component_iface()
            if comp:
                ext = comp.get_extents(Atspi.CoordType.SCREEN)
                x, y, w, h = ext.x, ext.y, ext.width, ext.height
            else:
                x, y, w, h = 0, 0, 0, 0
        except Exception:
            x, y, w, h = 0, 0, 0, 0
        if name and w > 0 and h > 0:
            results.append({"role": role, "name": name, "x": x, "y": y, "w": w, "h": h})
        for i in range(obj.get_child_count()):
            child = obj.get_child_at_index(i)
            if child:
                walk(child, depth + 1, results)
    except Exception:
        pass
    return results

desktop = Atspi.get_desktop(0)
all_elements = []
for i in range(desktop.get_child_count()):
    app_obj = desktop.get_child_at_index(i)
    if app_obj:
        app_name = app_obj.get_name() or ""
        target = APPFILTER
        if not target or target.lower() in app_name.lower():
            walk(app_obj, results=all_elements)
print(json.dumps(all_elements))
"""
        app_filter = repr(app) if app else "None"
        script = script.replace("APPFILTER", app_filter)

        # Use system python3 (not venv) because python3-gi is installed system-wide
        result = subprocess.run(
            ["/usr/bin/python3", "-c", script],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            return json.loads(result.stdout.strip())
    except Exception:
        pass
    return []


@click.command()
@click.option("--app", default=None, help="Target application name.")
@click.option("--screen", default=None, type=int, help="Screen index.")
@click.option("--ocr", "use_ocr", is_flag=True, help="Fallback to OCR if accessibility tree is empty.")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def see(app, screen, use_ocr, as_json):
    """Capture a screenshot and read the accessibility tree."""
    ensure_display()

    # Focus app if specified
    if app:
        search = subprocess.run(
            ["xdotool", "search", "--limit", "1", "--name", app],
            capture_output=True, text=True, timeout=5,
        )
        if search.returncode == 0 and search.stdout.strip():
            wid = search.stdout.strip().splitlines()[0]
            subprocess.run(["xdotool", "windowactivate", wid], capture_output=True, text=True, timeout=5)

    path = _screenshot(app=app, screen=screen)
    if not path:
        emit_error("Screenshot failed", as_json=as_json)

    store = ElementStore()
    raw_elements = _get_accessibility_tree(app=app)
    for el in raw_elements:
        store.add(el["role"], el["name"], el["x"], el["y"], el["w"], el["h"])

    # If no elements and OCR requested, run OCR
    if not store.elements and use_ocr:
        from commands.ocr import _run_ocr
        _run_ocr(path, store)

    data = {
        "ok": True,
        "screenshot": path,
        "elements": store.to_list(),
        "element_count": len(store.elements),
    }

    human = f"Screenshot: {path} ({len(store.elements)} elements)"
    emit(data, as_json=as_json, human_lines=human)
