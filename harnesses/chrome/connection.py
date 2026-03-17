"""Chrome DevTools Protocol connection via raw websockets.

No heavy dependencies — uses httpx for /json endpoint and websockets for CDP.
"""

import json
import sys
from contextlib import asynccontextmanager

import httpx
import websockets


def list_targets(host: str = "127.0.0.1", port: int = 9222) -> list[dict]:
    """List all debuggable targets (pages/tabs) via CDP HTTP endpoint."""
    try:
        resp = httpx.get(f"http://{host}:{port}/json")
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.HTTPStatusError):
        print(
            f"Error: Cannot connect to Chrome on {host}:{port}. "
            "Is Chrome running with --remote-debugging-port=9222?",
            file=sys.stderr,
        )
        raise SystemExit(1)


def get_page_ws_url(host: str = "127.0.0.1", port: int = 9222, tab_index: int = 0) -> str:
    """Get the WebSocket URL for a specific tab."""
    targets = list_targets(host, port)
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        print("Error: No page targets found", file=sys.stderr)
        raise SystemExit(1)
    if tab_index >= len(pages):
        print(f"Error: tab index {tab_index} out of range (0-{len(pages)-1})", file=sys.stderr)
        raise SystemExit(1)
    return pages[tab_index]["webSocketDebuggerUrl"]


class CDPSession:
    """Simple CDP session over websocket."""

    def __init__(self, ws):
        self._ws = ws
        self._id = 0

    async def send(self, method: str, params: dict | None = None) -> dict:
        """Send a CDP command and wait for the response."""
        self._id += 1
        msg = {"id": self._id, "method": method}
        if params:
            msg["params"] = params
        await self._ws.send(json.dumps(msg))
        # Wait for matching response
        while True:
            raw = await self._ws.recv()
            data = json.loads(raw)
            if data.get("id") == self._id:
                if "error" in data:
                    raise RuntimeError(f"CDP error: {data['error']}")
                return data.get("result", {})


@asynccontextmanager
async def connect(host: str = "127.0.0.1", port: int = 9222, tab_index: int = 0):
    """Connect to a Chrome tab via CDP websocket."""
    ws_url = get_page_ws_url(host, port, tab_index)
    async with websockets.connect(ws_url) as ws:
        yield CDPSession(ws)
