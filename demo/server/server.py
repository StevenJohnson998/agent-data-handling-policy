"""
ADHP Demo — MCP Server with ADHP Extension

A minimal MCP-compatible server that responds to `initialize` requests
with ADHP (Agent Data Handling Policy) fields in the capabilities object.

Security:
- Only accepts POST on /mcp
- Only handles `initialize`, `notifications/initialized`, and `ping` methods
- Rate limited per IP (10 req/min)
- Max request body 4KB
- Strict JSON-RPC 2.0 validation
- Binds to 127.0.0.1 only (use reverse proxy for public access)
"""

import json
import time
import logging
import asyncio
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_BODY_SIZE = 4096  # 4KB
RATE_LIMIT_MAX = 10   # requests per window
RATE_LIMIT_WINDOW = 60  # seconds

CONFIG_PATH = Path(__file__).parent / "adhp-config.json"
with open(CONFIG_PATH) as f:
    ADHP_CONFIG = json.load(f)

SERVER_NAME = ADHP_CONFIG.get("server_name", "ADHP Demo Server")
SERVER_VERSION = ADHP_CONFIG.get("server_version", "0.1.0")
ADHP_POLICY = ADHP_CONFIG["adhp"]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("adhp-demo")

# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-IP)
# ---------------------------------------------------------------------------

rate_limit_store: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if t > window_start
    ]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return True
    rate_limit_store[client_ip].append(now)
    return False


def cleanup_rate_limits():
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    stale = [ip for ip, times in rate_limit_store.items()
             if all(t <= window_start for t in times)]
    for ip in stale:
        del rate_limit_store[ip]


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

def jsonrpc_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def jsonrpc_result(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# ---------------------------------------------------------------------------
# MCP initialize handler
# ---------------------------------------------------------------------------

def handle_initialize(req_id, params: dict) -> dict:
    """
    MCP initialize response with ADHP extension.

    Follows MCP spec (2025-03-26):
    - protocolVersion: date-based version
    - capabilities: server features + ADHP extension
    - serverInfo: name and version
    """
    client_info = params.get("clientInfo", {})
    logger.info(
        f"Initialize from {client_info.get('name', 'unknown')} "
        f"(protocol: {params.get('protocolVersion', 'unknown')})"
    )

    return jsonrpc_result(req_id, {
        "protocolVersion": "2025-03-26",
        "capabilities": {
            "tools": {"listChanged": True},
            "resources": {},
            # --- ADHP extension ---
            "adhp": ADHP_POLICY,
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    })


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ADHP Demo MCP Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    client_ip = request.client.host if request.client else "unknown"

    # Rate limiting
    if is_rate_limited(client_ip):
        logger.warning(f"Rate limited: {client_ip}")
        return JSONResponse(
            status_code=429,
            content=jsonrpc_error(None, -32000, "Rate limit exceeded. Max 10 requests per minute."),
        )

    # Body size check (header)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content=jsonrpc_error(None, -32000, f"Request too large. Max {MAX_BODY_SIZE} bytes."),
        )

    # Read and parse body
    try:
        body = await request.body()
        if len(body) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content=jsonrpc_error(None, -32000, f"Request too large. Max {MAX_BODY_SIZE} bytes."),
            )
        data = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content=jsonrpc_error(None, -32700, "Parse error: invalid JSON."),
        )

    # Validate JSON-RPC structure
    if not isinstance(data, dict):
        return JSONResponse(
            status_code=400,
            content=jsonrpc_error(None, -32600, "Invalid request: expected JSON object."),
        )

    if data.get("jsonrpc") != "2.0":
        return JSONResponse(
            status_code=400,
            content=jsonrpc_error(data.get("id"), -32600, "jsonrpc must be '2.0'."),
        )

    req_id = data.get("id")
    method = data.get("method")
    params = data.get("params", {})

    if not isinstance(method, str):
        return JSONResponse(
            status_code=400,
            content=jsonrpc_error(req_id, -32600, "method must be a string."),
        )

    # Method dispatch — whitelist only
    if method == "initialize":
        return JSONResponse(content=handle_initialize(req_id, params))

    elif method == "notifications/initialized":
        logger.info(f"Client initialized from {client_ip}")
        return Response(status_code=202)

    elif method == "ping":
        return JSONResponse(content=jsonrpc_result(req_id, {}))

    else:
        logger.info(f"Rejected method '{method}' from {client_ip}")
        return JSONResponse(
            status_code=400,
            content=jsonrpc_error(req_id, -32601, f"Method not found: '{method}'. Only 'initialize' is supported."),
        )


@app.api_route("/mcp", methods=["GET", "PUT", "DELETE", "PATCH"])
async def reject_non_post():
    return JSONResponse(status_code=405, content={"error": "POST only."})


@app.get("/health")
async def health():
    return {"status": "ok", "server": SERVER_NAME}


@app.on_event("startup")
async def startup():
    async def periodic_cleanup():
        while True:
            cleanup_rate_limits()
            await asyncio.sleep(300)
    asyncio.create_task(periodic_cleanup())
    logger.info(f"ADHP Demo MCP Server started: {SERVER_NAME} v{SERVER_VERSION}")
    logger.info(f"ADHP Level: {ADHP_POLICY.get('level', 'not set')}")
