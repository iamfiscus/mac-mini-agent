"""OCR — extract text from screen via tesseract."""

import os
import subprocess
import uuid

import click

from modules.display import ensure_display
from modules.elements import ElementStore
from modules.output import emit, emit_error


def _run_ocr(image_path: str, store: ElementStore) -> None:
    """Run tesseract on an image and populate the element store."""
    # Use tesseract with TSV output for bounding boxes
    result = subprocess.run(
        ["tesseract", image_path, "stdout", "--psm", "11", "tsv"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:
        return

    # Parse TSV: level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
    header = lines[0].split("\t")
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 12:
            continue
        text = parts[11].strip()
        conf = int(parts[10]) if parts[10].strip().lstrip("-").isdigit() else 0
        if not text or conf < 30:
            continue
        left = int(parts[6])
        top = int(parts[7])
        width = int(parts[8])
        height = int(parts[9])
        if width > 0 and height > 0:
            store.add_ocr(text, left, top, width, height)


@click.command()
@click.option("--app", default=None, help="Target application name.")
@click.option("--store", "do_store", is_flag=True, help="Store OCR results as clickable elements (O1, O2, etc.).")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def ocr(app, do_store, as_json):
    """Extract text from screen via OCR (tesseract)."""
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

    # Screenshot
    os.makedirs("/tmp/steer", exist_ok=True)
    path = f"/tmp/steer/{uuid.uuid4().hex[:8]}.png"
    cmd = ["scrot", "-u", path] if app else ["scrot", path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        emit_error("Screenshot failed", as_json=as_json)

    store = ElementStore()
    _run_ocr(path, store)

    data = {
        "ok": True,
        "screenshot": path,
        "elements": store.to_list() if do_store else [],
        "text": [e.label for e in store.elements],
        "element_count": len(store.elements),
    }

    human_lines = "\n".join(
        f"  {e.id}: {e.label} ({e.x},{e.y})" if do_store else f"  {e.label}"
        for e in store.elements
    )
    human = f"Screenshot: {path}\nOCR ({len(store.elements)} elements):\n{human_lines}"
    emit(data, as_json=as_json, human_lines=human)
