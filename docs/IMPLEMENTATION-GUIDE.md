# ADHP Implementation Guide

> **Status:** Living document — evolves with the ecosystem
> **Prerequisites:** Read the [README](README.md) for context and [SPEC.md](SPEC.md) for the full specification.

---

## Quick Start

### Declaring ADHP (server-side)

Add an `adhp` object to your MCP server's `initialize` response or your A2A Agent Card:

```json
{
  "capabilities": {
    "adhp": {
      "level": "strict",
      "training_opt_out": true,
      "max_retention": "request",
      "compliance": ["GDPR"],
      "processing_jurisdiction": ["DE"]
    }
  }
}
```

All available fields → [SPEC.md §4](SPEC.md#4-data-handling-properties)

### Checking ADHP (client-side)

Read the `adhp` capability from the server's `initialize` response. Compare against your requirements **before sending any data**. If the server doesn't meet requirements, refuse the connection.

### Using the SDK (coming soon)

```python
# Server: declare your policy
from adhp import ADHPServer
server = ADHPServer(name="MyAgent", config="adhp-config.json")

# Client: check compliance
from adhp import ADHPClient
client = ADHPClient(requirements={"min_level": "strict", "require_compliance": ["GDPR"]})
result = client.check("http://server/mcp")

# CLI
adhp check http://server/mcp --min-level strict --require-compliance GDPR
```

### Examples

- [mcp-handshake.json](examples/mcp-handshake.json) — ADHP in an MCP initialize response
- [a2a-agent-card.json](examples/a2a-agent-card.json) — ADHP in an A2A Agent Card
- [orchestrator-query.md](examples/orchestrator-query.md) — How an orchestrator queries by trust level

---

## Enforcement Layers

ADHP declarations can be enforced at multiple layers. Each adds assurance — no single layer is sufficient on its own.

| Layer | What it does | When to use |
|-------|-------------|-------------|
| **Client-side** | Client reads ADHP in handshake, disconnects if insufficient | Minimum viable — any MCP client can do this today |
| **Gateway** | Proxy checks ADHP before routing, blocks non-compliant connections | Organizational policy enforcement, audit trails |
| **Registry** | Filters agents at discovery time by ADHP metadata | Trust-based discovery, delegation chain validation |
| **Runtime** | Containers/TEEs constrain what agents can physically do | Backing Level 3-4 declarations with infrastructure |
| **Cryptographic** | Signed code, encrypted envelopes, TEE attestation | Future — Phase 4 of the verification roadmap |

The strongest posture combines multiple layers. For detailed patterns, see the [enforcement discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5).

---

## Suggested Runtime Patterns by Level

| ADHP Level | Suggested implementation |
|------------|------------------------|
| Level 0-1 | Standard server with logging configuration |
| Level 2 | Containerized execution, PII tokenization proxy |
| Level 3 | Isolated containers, output validation, no persistent storage |
| Level 4 | Trusted Execution Environment (AWS Nitro, Intel SGX, AMD SEV) with memory-only processing |

These are suggestions, not requirements. Operators choose their own implementation as long as the declared level is met. The key principle: **higher levels require stronger infrastructure backing to be credible.**

---

## Jurisdiction Checking Logic

Server jurisdiction fields declare where data **may** go. Client accepted jurisdictions define where data is **allowed** to go.

**Rules:**
1. All server-declared jurisdictions must be within the client's accepted list
2. Undeclared server jurisdiction = fail (assume worst case)
3. Gateways can raise requirements but never lower them
4. The most restrictive requirement in the chain wins

**Example:** Server declares `processing_jurisdiction: ["DE", "US"]`. Client accepts `["DE", "FR"]`. Result: **FAIL** — the server may process in the US, which is not in the client's accepted list.

> v0.3 will add `guaranteed` vs. `possible` jurisdiction modeling for multi-region providers.

---

## Contributing

Implementation patterns are evolving fast. If you're building ADHP enforcement into a gateway, registry, or runtime, join the [discussions](../../discussions).

**Key discussions:**
- [Architecture — where ADHP sits in the stack](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6)
- [Enforcement patterns — honest assessment of each approach](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5)
- [Jurisdiction modeling challenges](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/7)
