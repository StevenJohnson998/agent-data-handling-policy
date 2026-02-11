# Agent Data Handling Policy (ADHP)

[![ADHP Validator](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml/badge.svg)](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml)

**A privacy label for AI agents.**

When an AI agent processes your data, what happens to it? Does it get stored? Used for training? Forwarded to a third party? Today, there's no standard way to know.

ADHP is an open specification that lets AI agents declare their data handling practices in a machine-readable format — GDPR's Article 13 (transparency) designed for agent-to-agent communication.

```json
{
  "adhp": {
    "level": "strict",
    "training_opt_out": true,
    "max_retention": "request",
    "compliance": ["GDPR", "HIPAA"],
    "pii_categories": ["email", "financial", "health"],
    "processing_jurisdiction": ["DE"],
    "third_party_opt_out": true
  }
}
```

> **🎮 [Try the interactive playground](https://iamagique.dev/adhp-demo/playground)** — configure client requirements and server declarations, then see ADHP compliance checking in action.

---

## Why This Matters

AI agents are multiplying — MCP has 97M+ monthly SDK downloads, Google's A2A connects agents to agents — but **no protocol answers what an agent does with your data.** There is no regulation specifically covering agent-to-agent data flows, which means agent suppliers risk unknowingly breaking GDPR, HIPAA, or the EU AI Act every time data crosses an agent boundary without documented handling practices.

ADHP closes this gap with five levels and a set of machine-readable properties that orchestrators, gateways, and registries can check automatically — before any data is sent.

---

## The Five Levels

| Level | Label | What It Means |
|-------|-------|---------------|
| 0 | **open** | No promises. Data may be used for anything including training, stored indefinitely, shared freely. |
| 1 | **standard** | No training. Defined retention. Metadata logging only. |
| 2 | **sensitive** | No training. Short retention. PII protected. Output sanitized. |
| 3 | **strict** | No logging, no third-party sharing. Delegation only to same level or above. |
| 4 | **zero-trace** | Memory-only processing. No disk writes. No logs. No delegation. |

No declaration = **assume Level 0** (worst case). Full level definitions and all properties (jurisdiction, retention, PII, delegation, environment, etc.): [SPEC.md](SPEC.md)

---

## Architecture — A Cross-Cutting Concern

ADHP extends multiple layers of the agentic stack simultaneously — like TLS in web architecture:

```
┌─────────────────────────────────────────────────┐
│  External Interactions                           │
│  Tools, APIs, other agents, commerce...          │
├─────────────────────────────────────────────────┤
│  Registry & Trust                              ◄── ADHP: filterable trust metadata
├─────────────────────────────────────────────────┤
│  Runtime                                         │
│  Secure execution, sandboxing, TEE               │
├─────────────────────────────────────────────────┤
│  Enforcement Gateway                           ◄── ADHP: machine-readable policy rules
├─────────────────────────────────────────────────┤
│  Protocol: MCP + A2A                           ◄── ADHP: data handling declarations
└─────────────────────────────────────────────────┘
```

Deep dive: [Architecture discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6)

---

## How It Works

During the MCP `initialize` handshake, a server declares its ADHP policy inside `capabilities`. The client (or gateway) checks it **before sending any data** — if the server doesn't meet requirements, the connection is refused. ADHP also extends [A2A Agent Cards](https://google.github.io/A2A/). See the [full specification](SPEC.md) and [example handshake JSON](examples/mcp-handshake.json).

**Delegation cascading:** when Agent A delegates to Agent B, the privacy level must meet or exceed what the **caller originally requested** — not just the delegating agent's own level. Gateways can raise requirements but never lower them. Level 4 agents cannot delegate at all — zero-trace means data never leaves the agent boundary. Details: [SPEC.md §5](SPEC.md#5-delegation-cascading-rule)

**Enforcement:** ADHP is declarative — agents declare what they promise. Gateways block non-compliant connections at runtime, registries filter at discovery, and runtime environments (containers, TEEs) physically constrain data handling. The [verification roadmap](SPEC.md#7-verification-roadmap) progresses from self-declaration to cryptographic guarantees. See the [enforcement discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5).

---

## Try It

**[Interactive Playground](https://iamagique.dev/adhp-demo/playground)** — configure MCP client/gateway requirements and server ADHP declarations in your browser.

**Validate a delegation chain:** `python tools/validate_chain.py`

**Examples:** [agent manifests](examples/agent-manifest.json), [MCP handshake](examples/mcp-handshake.json), [A2A agent card](examples/a2a-agent-card.json), [delegation scenarios](examples/delegation-chain.md), [orchestrator queries](examples/orchestrator-query.md)

---

## Project Status

**Version:** 0.2.0 (Draft) · **License:** Apache 2.0

This specification is a draft seeking community feedback. Not yet an official standard or MCP extension.

**Roadmap:**
1. Community feedback on the spec (current)
2. Reference implementation in [Agent Registry](https://github.com/StevenJohnson998/agent-registry)
3. Propose as MCP Extension (via SEP process)
4. Seek AAIF adoption

**v0.3 planned:**
- Jurisdiction modeling: guaranteed vs. possible locations ([discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/7))
- DPA verification: cryptographic proof of legal agreements at runtime ([discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/8))

**v0.4 planned:**
- Cryptographic DPA verification layer: runtime challenge-response proof that valid DPAs exist across the delegation chain
- Zero-knowledge chain propagation: clients see whether the full chain is DPA-verified without seeing intermediate details
- Prerequisites: v0.3 bidirectional handshake
- Interactive playground improvements
- Gateway policy language specification

---

## Contributing
- [DPA verification — cryptographic proof of legal agreements](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/8)

We're looking for feedback on the levels, delegation rules, verification mechanisms, and regulatory interactions. See the open discussions:

- [Architecture — where ADHP sits in the stack](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6)
- [Jurisdiction modeling](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/7)
- [Enforcement patterns](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5)

Open a [Discussion](../../discussions) for ideas, an [Issue](../../issues) for bugs, or submit a PR (open an issue first).
