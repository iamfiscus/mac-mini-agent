import httpx


def start_job(url: str, prompt: str) -> dict:
    """POST to url/job with prompt, returns response dict."""
    response = httpx.post(f"{url}/job", json={"prompt": prompt})
    response.raise_for_status()
    return response.json()


def get_job(url: str, job_id: str) -> str:
    """GET url/job/{job_id}, returns YAML content."""
    response = httpx.get(f"{url}/job/{job_id}")
    response.raise_for_status()
    return response.text


def list_jobs(url: str, archived: bool = False) -> str:
    """GET url/jobs, returns YAML content."""
    params = {"archived": "true"} if archived else {}
    response = httpx.get(f"{url}/jobs", params=params)
    response.raise_for_status()
    return response.text


def clear_jobs(url: str) -> dict:
    """POST url/jobs/clear, returns response dict."""
    response = httpx.post(f"{url}/jobs/clear")
    response.raise_for_status()
    return response.json()


def latest_jobs(url: str, n: int = 1) -> str:
    """GET the full details of the latest N jobs."""
    import yaml

    response = httpx.get(f"{url}/jobs")
    response.raise_for_status()
    data = yaml.safe_load(response.text)
    jobs = data.get("jobs") or []
    # Jobs are sorted by file order; take the last N (most recent)
    latest = jobs[-n:] if n < len(jobs) else jobs
    latest.reverse()  # Most recent first

    parts = []
    for job in latest:
        job_id = job["id"]
        detail = httpx.get(f"{url}/job/{job_id}")
        detail.raise_for_status()
        parts.append(detail.text)
    return "---\n".join(parts)


def stop_job(url: str, job_id: str) -> dict:
    """DELETE url/job/{job_id}, returns response dict."""
    response = httpx.delete(f"{url}/job/{job_id}")
    response.raise_for_status()
    return response.json()


# --- Brain-based routing ---

import json as json_mod
import os


def _brain_mcp_url() -> str:
    return os.environ.get("BRAIN_MCP_URL", "http://gertie.local:3300/mcp")


def _brain_key() -> str:
    return os.environ.get("BRAIN_KEY", "")


def _parse_sse(text: str):
    """Parse SSE or plain JSON response."""
    for line in text.splitlines():
        if line.startswith("data: "):
            return json_mod.loads(line[6:])
    try:
        return json_mod.loads(text)
    except Exception:
        return None


def _mcp_call_sync(tool: str, args: dict) -> dict | None:
    """Synchronous MCP tool call to brain."""
    url = _brain_mcp_url()
    key = _brain_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    # Initialize session
    init_resp = httpx.post(url, headers=headers, json={
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "direct-cli", "version": "0.1.0"}},
    })
    if init_resp.status_code != 200:
        return None
    session_id = init_resp.headers.get("mcp-session-id", "")
    # Send initialized notification
    httpx.post(url, headers={**headers, "Mcp-Session-Id": session_id}, json={
        "jsonrpc": "2.0", "method": "notifications/initialized",
    })
    # Call tool
    resp = httpx.post(url, headers={**headers, "Mcp-Session-Id": session_id}, json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    })
    if resp.status_code == 200:
        data = _parse_sse(resp.text)
        return data.get("result") if data else None
    return None


def route_job(prompt: str, requires: list[str], agent: str = "claude") -> dict:
    """Route a job to the best available device based on capabilities.

    Queries brain for online agents, filters by required capabilities,
    picks the first match, and sends the job to its Listen URL.
    """
    try:
        result = _mcp_call_sync("brain_who", {})
    except Exception as e:
        raise RuntimeError(f"Brain unreachable at {_brain_mcp_url()}: {e}")
    if not result or "content" not in result:
        raise RuntimeError("brain_who returned no data")

    # Parse the brain_who response — expect content with agent list
    content = result.get("content", [])
    agents_text = ""
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            agents_text = item["text"]
            break

    if not agents_text:
        raise RuntimeError("No agents online")

    # brain_who returns JSON with online agents
    try:
        agents_data = json_mod.loads(agents_text)
    except json_mod.JSONDecodeError:
        raise RuntimeError(f"Could not parse brain_who response: {agents_text[:200]}")

    # agents_data is a list of dicts with name, capabilities, listen_url, etc.
    agents = agents_data if isinstance(agents_data, list) else agents_data.get("agents", [])

    # Device listen URLs — fallback lookup if not in brain response
    DEVICE_URLS = {
        "hal9000": "http://100.113.65.70:7600",
        "macbook": "http://localhost:7600",
    }

    for ag in agents:
        caps = set(ag.get("capabilities", []))
        if set(requires).issubset(caps):
            name = ag.get("name", "")
            listen_url = ag.get("listen_url") or DEVICE_URLS.get(name)
            if listen_url:
                return start_job(listen_url, prompt)

    available = [f"{a.get('name')}: {a.get('capabilities', [])}" for a in agents]
    raise RuntimeError(
        f"No device matches capabilities {requires}. "
        f"Online: {'; '.join(available) or 'none'}"
    )
