"""ADHPServer — wraps FastMCP to inject ADHP policy into MCP capabilities.

Provides two modes:
  Mode A: Full wrapper around FastMCP (recommended)
  Mode B: Manual injection for existing servers via ADHPPolicy.to_dict()
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_policy
from .models import ADHPPolicy


class ADHPServer:
    """MCP server with built-in ADHP policy declaration.

    Wraps the FastMCP server and injects ADHP fields into the
    ``initialize`` response capabilities.

    Usage::

        from adhp import ADHPServer

        server = ADHPServer(name="MyServer", config="adhp-config.json")

        @server.tool()
        def my_tool(data: str) -> str:
            return "processed"

        server.run()
    """

    def __init__(
        self,
        name: str = "ADHP Server",
        version: str = "1.0.0",
        config: str | Path | dict | ADHPPolicy | None = None,
        policy: ADHPPolicy | None = None,
        **fastmcp_kwargs: Any,
    ):
        """Initialize ADHPServer.

        Args:
            name: Server name.
            version: Server version.
            config: Path to config file, dict, or ADHPPolicy. Mutually
                    exclusive with ``policy``.
            policy: ADHPPolicy instance directly. Mutually exclusive with
                    ``config``.
            **fastmcp_kwargs: Extra kwargs passed to FastMCP constructor.
        """
        if config is not None and policy is not None:
            raise ValueError("Provide either config or policy, not both")

        if policy is not None:
            self._policy = policy
        elif config is not None:
            self._policy = load_policy(config)
        else:
            raise ValueError("Either config or policy must be provided")

        self._name = name
        self._version = version
        self._fastmcp_kwargs = fastmcp_kwargs
        self._mcp = None
        self._tools: list[Any] = []
        self._resources: list[Any] = []
        self._prompts: list[Any] = []

    @property
    def policy(self) -> ADHPPolicy:
        """The ADHP policy for this server."""
        return self._policy

    def _ensure_mcp(self):
        """Lazily create the FastMCP instance."""
        if self._mcp is not None:
            return
        try:
            from fastmcp import FastMCP
        except ImportError:
            raise ImportError(
                "fastmcp is required for ADHPServer. Install with: pip install adhp[server] or pip install fastmcp"
            )
        self._mcp = FastMCP(self._name, **self._fastmcp_kwargs)

    def tool(self, *args, **kwargs):
        """Decorator to register a tool (delegates to FastMCP.tool)."""
        self._ensure_mcp()
        return self._mcp.tool(*args, **kwargs)

    def resource(self, *args, **kwargs):
        """Decorator to register a resource (delegates to FastMCP.resource)."""
        self._ensure_mcp()
        return self._mcp.resource(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        """Decorator to register a prompt (delegates to FastMCP.prompt)."""
        self._ensure_mcp()
        return self._mcp.prompt(*args, **kwargs)

    def get_adhp_capabilities(self) -> dict:
        """Return the ADHP policy as a dict for MCP capabilities."""
        return self._policy.to_dict()

    def run(self, transport: str = "streamable-http", host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server with ADHP capabilities.

        For MVP, this uses a lightweight FastAPI wrapper that injects ADHP
        into the MCP initialize response, since FastMCP doesn't natively
        support custom capabilities in the initialize response.
        """
        self._run_http(host, port)

    def _run_http(self, host: str, port: int):
        """Run as an HTTP MCP server with ADHP in capabilities."""
        try:
            import uvicorn
            from starlette.applications import Starlette
            from starlette.requests import Request
            from starlette.responses import JSONResponse
            from starlette.routing import Route
        except ImportError:
            raise ImportError(
                "starlette and uvicorn required for HTTP mode. "
                "Install with: pip install adhp[server]"
            )

        adhp_caps = self.get_adhp_capabilities()
        server_name = self._name
        server_version = self._version
        policy_level = self._policy.level

        async def mcp_endpoint(request: Request) -> JSONResponse:
            body = await request.json()
            method = body.get("method", "")
            req_id = body.get("id")

            if method == "initialize":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {},
                            "adhp": adhp_caps,
                        },
                        "serverInfo": {
                            "name": server_name,
                            "version": server_version,
                        },
                    },
                })
            elif method == "notifications/initialized":
                return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})
            elif method == "ping":
                return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {}})
            else:
                return JSONResponse(
                    {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}},
                    status_code=200,
                )

        async def health(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok", "adhp_level": policy_level})

        async def adhp_info(request: Request) -> JSONResponse:
            return JSONResponse(adhp_caps)

        app = Starlette(routes=[
            Route("/mcp", mcp_endpoint, methods=["POST"]),
            Route("/health", health, methods=["GET"]),
            Route("/adhp", adhp_info, methods=["GET"]),
        ])

        uvicorn.run(app, host=host, port=port)
