import asyncio
import logging
import os
import shutil
import signal
import subprocess
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("listen")

# --- Brain configuration ---
BRAIN_MCP_URL = os.environ.get("BRAIN_MCP_URL", "http://gertie.local:3300/mcp")
BRAIN_KEY = os.environ.get("BRAIN_KEY", "")
DEVICE_ID = os.environ.get("DEVICE_ID", "hal9000")
# BRAIN_URL kept for reference but MCP is the primary interface
BRAIN_URL = BRAIN_MCP_URL


def _parse_sse(text: str) -> dict | None:
    """Parse SSE response to extract JSON from 'data:' line."""
    import json as json_mod
    for line in text.splitlines():
        if line.startswith("data: "):
            return json_mod.loads(line[6:])
    # Maybe it's plain JSON
    try:
        return json_mod.loads(text)
    except Exception:
        return None


async def _mcp_call(client: "httpx.AsyncClient", session_id: str, tool: str, args: dict, req_id: int = 1) -> dict | None:
    """Call a brain MCP tool via streamable HTTP."""
    headers = {
        "Authorization": f"Bearer {BRAIN_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session_id,
    }
    resp = await client.post(BRAIN_URL, headers=headers, json={
        "jsonrpc": "2.0", "id": req_id, "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    })
    if resp.status_code == 200:
        data = _parse_sse(resp.text)
        return data.get("result") if data else None
    return None


async def _mcp_initialize(client: "httpx.AsyncClient") -> str | None:
    """MCP initialize handshake. Returns session ID."""
    headers = {
        "Authorization": f"Bearer {BRAIN_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    resp = await client.post(BRAIN_URL, headers=headers, json={
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": DEVICE_ID, "version": "0.1.0"}},
    })
    if resp.status_code == 200:
        session_id = resp.headers.get("mcp-session-id", "")
        # Send initialized notification
        await client.post(BRAIN_URL, headers={**headers, "Mcp-Session-Id": session_id}, json={
            "jsonrpc": "2.0", "method": "notifications/initialized",
        })
        return session_id
    return None


async def _brain_register():
    """Register this device with the brain via MCP. Fire-and-forget."""
    if not BRAIN_KEY:
        return
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            session_id = await _mcp_initialize(client)
            if session_id:
                await _mcp_call(client, session_id, "brain_register", {
                    "name": DEVICE_ID,
                    "role": "device-agent",
                    "capabilities": ["terminal", "gui-x11", "claude", "opencode"],
                })
                logger.info(f"Brain: registered as {DEVICE_ID}")
    except Exception as e:
        logger.warning(f"Brain: register failed (non-blocking): {e}")


async def _brain_heartbeat_loop():
    """Send heartbeat every 10s. Brain presence expires after 15s.

    Re-initializes the MCP session if the heartbeat fails, since
    sessions can expire or be dropped by the server.
    """
    if not BRAIN_KEY:
        return
    import httpx
    while True:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                session_id = await _mcp_initialize(client)
                if not session_id:
                    logger.warning("Brain: heartbeat MCP init failed, retrying in 10s")
                    await asyncio.sleep(10)
                    continue
                logger.info(f"Brain: heartbeat session established ({session_id[:8]}...)")
                while True:
                    result = await _mcp_call(client, session_id, "brain_heartbeat", {
                        "status": "online",
                        "current_task": "listening",
                    })
                    if result is None:
                        logger.warning("Brain: heartbeat call failed, re-initializing")
                        break  # break inner loop to re-init session
                    await asyncio.sleep(10)
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.warning(f"Brain: heartbeat error ({e}), retrying in 10s")
            await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app):
    """Register with brain on startup, heartbeat while running."""
    await _brain_register()
    heartbeat_task = asyncio.create_task(_brain_heartbeat_loop())
    yield
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

JOBS_DIR = Path(__file__).parent / "jobs"
JOBS_DIR.mkdir(exist_ok=True)
ARCHIVED_DIR = JOBS_DIR / "archived"


class JobRequest(BaseModel):
    prompt: str
    agent: str = "claude"  # claude | opencode | pi


@app.post("/job")
def create_job(req: JobRequest):
    job_id = uuid4().hex[:8]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    job_data = {
        "id": job_id,
        "status": "running",
        "prompt": req.prompt,
        "agent": req.agent,
        "created_at": now,
        "pid": 0,
        "updates": [],
        "summary": "",
    }

    # Write YAML before spawning worker (worker reads it on startup)
    job_file = JOBS_DIR / f"{job_id}.yaml"
    with open(job_file, "w") as f:
        yaml.dump(job_data, f, default_flow_style=False, sort_keys=False)

    # Spawn the worker process
    worker_path = Path(__file__).parent / "worker.py"
    proc = subprocess.Popen(
        [sys.executable, str(worker_path), job_id, req.prompt, req.agent],
        cwd=str(Path(__file__).parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Update PID after spawn
    job_data["pid"] = proc.pid
    with open(job_file, "w") as f:
        yaml.dump(job_data, f, default_flow_style=False, sort_keys=False)

    return {"job_id": job_id, "status": "running"}


@app.get("/job/{job_id}", response_class=PlainTextResponse)
def get_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    return job_file.read_text()


@app.get("/jobs", response_class=PlainTextResponse)
def list_jobs(archived: bool = False):
    search_dir = ARCHIVED_DIR if archived else JOBS_DIR
    jobs = []
    for f in sorted(search_dir.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
        jobs.append({
            "id": data.get("id"),
            "status": data.get("status"),
            "prompt": data.get("prompt"),
            "created_at": data.get("created_at"),
        })
    result = yaml.dump({"jobs": jobs}, default_flow_style=False, sort_keys=False)
    return result


@app.post("/jobs/clear")
def clear_jobs():
    ARCHIVED_DIR.mkdir(exist_ok=True)
    count = 0
    for f in JOBS_DIR.glob("*.yaml"):
        shutil.move(str(f), str(ARCHIVED_DIR / f.name))
        count += 1
    return {"archived": count}


@app.delete("/job/{job_id}")
def stop_job(job_id: str):
    job_file = JOBS_DIR / f"{job_id}.yaml"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    with open(job_file) as f:
        data = yaml.safe_load(f)

    pid = data.get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    data["status"] = "stopped"
    with open(job_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    return {"job_id": job_id, "status": "stopped"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7600)
