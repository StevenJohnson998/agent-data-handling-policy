"""ADHPClient — connects to MCP servers and checks ADHP compliance."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .checker import check_compliance
from .config import load_requirements
from .exceptions import ADHPComplianceError, ADHPConnectionError
from .models import ADHPClientRequirements, ADHPPolicy, ComplianceResult


class ADHPClient:
    """Client that connects to MCP servers and verifies ADHP compliance.

    Usage::

        from adhp import ADHPClient

        client = ADHPClient(min_level="strict", require_compliance=["GDPR"])
        result = client.check("http://localhost:8000/mcp")

        if not result.compliant:
            for c in result.checks:
                if not c.passed:
                    print(f"FAIL: {c.name} — {c.reason}")
    """

    def __init__(
        self,
        requirements: str | Path | dict | ADHPClientRequirements | None = None,
        *,
        min_level: str = "open",
        require_compliance: list[str] | None = None,
        accepted_jurisdictions: list[str] | None = None,
        require_training_opt_out: bool = False,
        require_no_third_party: bool = False,
        max_retention: Optional[str] = None,
        require_content_logging_opt_out: bool = False,
    ):
        """Initialize ADHPClient.

        Either pass a ``requirements`` source (file/dict/object) OR set
        individual keyword arguments. If ``requirements`` is provided,
        keyword arguments are ignored.
        """
        if requirements is not None:
            self._requirements = load_requirements(requirements)
        else:
            self._requirements = ADHPClientRequirements(
                min_level=min_level,  # type: ignore[arg-type]
                require_compliance=require_compliance or [],
                accepted_jurisdictions=accepted_jurisdictions or [],
                require_training_opt_out=require_training_opt_out,
                require_no_third_party=require_no_third_party,
                max_retention=max_retention,  # type: ignore[arg-type]
                require_content_logging_opt_out=require_content_logging_opt_out,
            )

    @property
    def requirements(self) -> ADHPClientRequirements:
        return self._requirements

    def check(self, url: str, *, timeout: int = 10) -> ComplianceResult:
        """Connect to an MCP server and check its ADHP compliance.

        Args:
            url: The MCP endpoint URL (e.g., http://localhost:8000/mcp).
            timeout: Connection timeout in seconds.

        Returns:
            ComplianceResult with compliant flag and individual check details.
        """
        adhp_data = self._fetch_adhp(url, timeout=timeout)
        return check_compliance(self._requirements, adhp_data)

    def check_policy(self, policy: ADHPPolicy | dict | None) -> ComplianceResult:
        """Check compliance against a policy directly (no network call).

        Args:
            policy: ADHPPolicy, dict, or None.

        Returns:
            ComplianceResult.
        """
        return check_compliance(self._requirements, policy)

    def check_or_raise(self, url: str, *, timeout: int = 10) -> ComplianceResult:
        """Like check() but raises ADHPComplianceError on failure."""
        result = self.check(url, timeout=timeout)
        if not result.compliant:
            failed = [c for c in result.checks if not c.passed]
            reasons = "; ".join(f"{c.name}: {c.reason}" for c in failed)
            raise ADHPComplianceError(f"Server not compliant: {reasons}", checks=failed)
        return result

    def _fetch_adhp(self, url: str, timeout: int = 10) -> dict | None:
        """Send MCP initialize and extract ADHP from capabilities."""
        try:
            import httpx
        except ImportError:
            # Fall back to requests
            return self._fetch_adhp_requests(url, timeout)

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"roots": {"listChanged": True}},
                "clientInfo": {"name": "ADHP SDK Client", "version": "0.2.0"},
            },
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError as e:
            raise ADHPConnectionError(f"Connection failed: {url} — {e}") from e
        except httpx.TimeoutException as e:
            raise ADHPConnectionError(f"Timeout connecting to {url}") from e
        except httpx.HTTPStatusError as e:
            raise ADHPConnectionError(f"HTTP error from {url}: {e}") from e

        return self._extract_adhp(data)

    def _fetch_adhp_requests(self, url: str, timeout: int) -> dict | None:
        """Fallback using requests library."""
        import requests

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"roots": {"listChanged": True}},
                "clientInfo": {"name": "ADHP SDK Client", "version": "0.2.0"},
            },
        }

        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.ConnectionError as e:
            raise ADHPConnectionError(f"Connection failed: {url} — {e}") from e
        except requests.Timeout as e:
            raise ADHPConnectionError(f"Timeout connecting to {url}") from e
        except requests.HTTPError as e:
            raise ADHPConnectionError(f"HTTP error from {url}: {e}") from e

        return self._extract_adhp(data)

    @staticmethod
    def _extract_adhp(response: dict) -> dict | None:
        """Extract ADHP dict from MCP initialize response."""
        if "error" in response:
            raise ADHPConnectionError(
                f"Server returned error: {response['error'].get('message', 'unknown')}"
            )
        return (
            response.get("result", {})
            .get("capabilities", {})
            .get("adhp")
        )
