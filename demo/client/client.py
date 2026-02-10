"""
ADHP Demo — MCP Client

Sends an MCP `initialize` request to a server, reads the ADHP extension
from the response, and checks if the server meets the client's requirements.

Usage:
  python client.py                          # Use defaults
  python client.py --url http://localhost:8000/mcp
  python client.py --min-level sensitive --require-compliance GDPR
  python client.py --no-third-party
"""

import argparse
import json
import sys

import requests

# ---------------------------------------------------------------------------
# ADHP level ordering
# ---------------------------------------------------------------------------

LEVEL_ORDER = {
    "open": 0,
    "standard": 1,
    "sensitive": 2,
    "strict": 3,
    "zero-trace": 4,
}


def level_value(level_name: str) -> int:
    return LEVEL_ORDER.get(level_name, -1)


# ---------------------------------------------------------------------------
# MCP initialize request
# ---------------------------------------------------------------------------

def send_initialize(url: str) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "roots": {"listChanged": True},
            },
            "clientInfo": {
                "name": "ADHP Demo Client",
                "version": "0.1.0",
            },
        },
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        print(f"\n❌ Connection failed: could not reach {url}")
        sys.exit(1)
    except requests.Timeout:
        print(f"\n❌ Timeout: server at {url} did not respond within 10s")
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"\n❌ HTTP error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# ADHP compliance check
# ---------------------------------------------------------------------------

def check_adhp(adhp: dict, args) -> list[str]:
    failures = []

    server_level = adhp.get("level", "open")
    if level_value(server_level) < level_value(args.min_level):
        failures.append(
            f"Level too low: server is '{server_level}' "
            f"(level {level_value(server_level)}), "
            f"client requires '{args.min_level}' "
            f"(level {level_value(args.min_level)})"
        )

    if args.require_compliance:
        server_compliance = set(adhp.get("compliance", []))
        required = set(args.require_compliance)
        missing = required - server_compliance
        if missing:
            failures.append(
                f"Missing compliance: {', '.join(sorted(missing))} "
                f"(server declares: {', '.join(sorted(server_compliance)) or 'none'})"
            )

    if args.no_third_party:
        sharing = adhp.get("third_party_sharing", {})
        if sharing.get("enabled", True):
            failures.append("Third-party sharing is enabled (client requires disabled)")

    if args.require_no_training:
        if not adhp.get("training_opt_out", False):
            failures.append("Training opt-out not declared (client requires training_opt_out: true)")

    if args.require_jurisdiction:
        server_jurisdictions = set(adhp.get("processing_jurisdiction", []))
        required = set(args.require_jurisdiction)
        if not required.intersection(server_jurisdictions):
            failures.append(
                f"Jurisdiction mismatch: server processes in "
                f"{', '.join(sorted(server_jurisdictions)) or 'undeclared'}, "
                f"client requires {', '.join(sorted(required))}"
            )

    return failures


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_response(response: dict):
    result = response.get("result", {})
    server_info = result.get("serverInfo", {})
    capabilities = result.get("capabilities", {})
    adhp = capabilities.get("adhp")

    print("\n" + "=" * 60)
    print("MCP Initialize Response")
    print("=" * 60)
    print(f"  Protocol Version: {result.get('protocolVersion', 'unknown')}")
    print(f"  Server:           {server_info.get('name', 'unknown')} v{server_info.get('version', '?')}")

    std_caps = [k for k in capabilities if k != "adhp"]
    print(f"  Capabilities:     {', '.join(std_caps) if std_caps else 'none'}")

    if adhp:
        print("\n" + "-" * 60)
        print("ADHP Declaration")
        print("-" * 60)
        print(f"  Level:            {adhp.get('level', 'not declared')}")
        print(f"  Training opt-out: {adhp.get('training_opt_out', 'not declared')}")
        print(f"  Max retention:    {adhp.get('max_retention', 'not declared')}")
        print(f"  Content logging:  {adhp.get('content_logging', 'not declared')}")
        print(f"  Delegation:       {adhp.get('delegation_policy', 'not declared')}")
        print(f"  Compliance:       {', '.join(adhp.get('compliance', [])) or 'none declared'}")
        print(f"  PII categories:   {', '.join(adhp.get('pii_categories', [])) or 'none declared'}")
        print(f"  Jurisdiction:     {', '.join(adhp.get('processing_jurisdiction', [])) or 'not declared'}")
        sharing = adhp.get("third_party_sharing", {})
        print(f"  3rd-party sharing: {'enabled' if sharing.get('enabled') else 'disabled'}")
    else:
        print("\n  ⚠️  No ADHP declaration found — assume Level 0 (open)")

    print()


def print_result(failures: list[str], adhp: dict):
    if not failures:
        print("✅ PASS — Server meets all client ADHP requirements")
        print(f"   Server ADHP level: {adhp.get('level', 'unknown')}")
        print("   → Safe to send data.\n")
    else:
        print("❌ FAIL — Server does NOT meet client requirements")
        for f in failures:
            print(f"   ✗ {f}")
        print("   → Do NOT send data. Disconnect.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ADHP Demo Client — check MCP server ADHP compliance"
    )
    parser.add_argument("--url", default="http://localhost:8910/mcp")
    parser.add_argument("--min-level", default="standard", choices=LEVEL_ORDER.keys())
    parser.add_argument("--require-compliance", nargs="+", default=None)
    parser.add_argument("--no-third-party", action="store_true")
    parser.add_argument("--require-no-training", action="store_true")
    parser.add_argument("--require-jurisdiction", nargs="+", default=None)

    args = parser.parse_args()

    print(f"\n→ Sending MCP initialize to {args.url} ...")
    response = send_initialize(args.url)

    if "error" in response:
        print(f"\n❌ Server returned error: {response['error'].get('message', 'unknown')}")
        sys.exit(1)

    print_response(response)

    adhp = response.get("result", {}).get("capabilities", {}).get("adhp")

    if not adhp:
        print("❌ FAIL — No ADHP declaration. Assuming Level 0 (open).")
        print("   → Do NOT send sensitive data.\n")
        sys.exit(1)

    print("-" * 60)
    print(f"Checking requirements: min_level={args.min_level}", end="")
    if args.require_compliance:
        print(f", compliance={args.require_compliance}", end="")
    if args.no_third_party:
        print(", no_third_party=true", end="")
    if args.require_no_training:
        print(", no_training=true", end="")
    if args.require_jurisdiction:
        print(f", jurisdiction={args.require_jurisdiction}", end="")
    print("\n" + "-" * 60)

    failures = check_adhp(adhp, args)
    print_result(failures, adhp)

    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
