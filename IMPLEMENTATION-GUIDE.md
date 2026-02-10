# ADHP Implementation Guide

> **Status:** Living document — evolves with the ecosystem

## Overview

The [ADHP Specification](SPEC.md) defines *what* agents declare about their data handling. This guide covers *how* those declarations get implemented and enforced in practice.

Because the MCP gateway ecosystem is evolving rapidly, this guide intentionally stays high-level and points to community discussions where implementation patterns are tracked as they mature.

---

## Quick Start

**Declaring ADHP:** Add an `adhp` object to your MCP server's `initialize` response or your A2A Agent Card. See [SPEC.md, Section 4](SPEC.md#4-data-handling-properties) for all available fields.

**Checking ADHP:** As an MCP client or orchestrator, read the `adhp` capability from the server's `initialize` response. Compare against your requirements before sending any data.

**Examples:**
- [mcp-handshake.json](examples/mcp-handshake.json) — ADHP in an MCP initialize response
- [a2a-agent-card.json](examples/a2a-agent-card.json) — ADHP in an A2A Agent Card
- [orchestrator-query.md](examples/orchestrator-query.md) — How an orchestrator queries by trust level

---

## Enforcement Patterns

ADHP declarations can be enforced at multiple layers of the stack:

| Layer | What it does | When to use |
|-------|-------------|-------------|
| **Client-side** | Client reads ADHP in `initialize`, disconnects if insufficient | Minimum viable — any MCP client can do this today |
| **Gateway** | Proxy checks ADHP before routing, blocks non-compliant connections | Organizational policy enforcement, audit trails |
| **Registry** | Filters agents at discovery time by ADHP metadata | Trust-based discovery, delegation chain validation |
| **Runtime** | Containers/TEEs constrain what agents can physically do | Higher ADHP levels (Level 3-4) |
| **Cryptographic** | Encrypted envelopes, proofs of deletion, TEE attestation | Future — Phase 4 of the verification roadmap |

Each layer adds assurance. No single layer is sufficient on its own. The strongest posture combines multiple layers.

For detailed implementation patterns at each layer, including an honest assessment of what each approach can and cannot guarantee, see:

**→ [Implementation & enforcement patterns — from self-declaration to cryptographic guarantees](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5)**

---

## Architecture

ADHP is a cross-cutting concern that extends the protocol layer (MCP + A2A), the gateway layer, and the registry layer simultaneously. It is not a separate middleware or additional layer.

For the full architectural rationale and stack diagram, see:

**→ [ADHP architecture — a cross-cutting concern, not a layer](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6)**

---

## Runtime Patterns by Level

| ADHP Level | Suggested implementation |
|------------|------------------------|
| Level 0-1 | Standard server with logging configuration |
| Level 2 | Containerized execution, PII tokenization proxy between client and server |
| Level 3 | Isolated containers, output validation, no persistent storage |
| Level 4 | Trusted Execution Environment (AWS Nitro Enclaves, Intel SGX, AMD SEV) with memory-only processing |

These are suggestions, not requirements. Operators choose their own implementation as long as the declared level is met.

---

## Contributing

Implementation patterns are evolving fast. If you're building ADHP enforcement into a gateway, registry, or runtime, we'd love to hear about it — join the [discussions](../../discussions).
