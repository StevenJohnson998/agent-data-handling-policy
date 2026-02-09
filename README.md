# Agent Data Handling Policy (ADHP)

[![ADHP Validator](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml/badge.svg)](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml)

**A privacy label for AI agents.**

When you send data to an AI agent, what happens to it? Is it stored? Used for training? Forwarded somewhere else? Right now there's no standard way to know. ADHP fixes that — agents declare what they do with your data, and clients check before sending anything.

```json
{
  "adhp": {
    "level": "strict",
    "training_opt_out": true,
    "max_retention": "request",
    "compliance": ["GDPR", "HIPAA"],
    "pii_categories": ["email", "financial", "health"],
    "processing_jurisdiction": ["DE"],
    "third_party_sharing": { "enabled": false }
  }
}
```

An autonomous agent can read this and understand : no training on your data, deleted after each request, GDPR and HIPAA compliant, email/financial/health PII protected, processed in Germany, no third-party sharing.

---

## Why does this matter?

MCP and A2A are reshaping autonomous discovery and communication. But neither protocol answers a basic question: **what does this agent do with my data?**

**As a user :**

- Your service may have to choose between 50 agents for a task. How does it compare their privacy practices? It can't — there's no standard format.
- Your healthcare app needs to verify an agent won't train on patient data. Today that's a manual process for every single agent.
- Agent A delegates to Agent B. Nobody checks if the privacy chain holds.
- Your compliance team wants to audit data flows across your agent stack. Good luck without machine-readable policies.

**As a service provider :**

This isn't just about protecting your data when you *use* agents. If you *run* an AI service, you have the same problem in reverse.

Your users agreed to your privacy policy. They consented to specific terms. But the moment your service connects to an external MCP server, you inherit that server's data practices — and you probably have no idea what they are.

Today you have two options:

**Option A: Only use agents you've vetted.** Negotiate data handling agreements, review contracts, get legal involved. It's slow and expensive. Your pool of usable agents shrinks to whoever you've had time to negotiate with.

**Option B: Connect to whatever works.** Move fast, don't check. But if that server trains on content or shares data with third parties, you just breached your own privacy policy. Depending on where you operate, that could mean GDPR Article 28 violations, HIPAA issues, or worse.

**ADHP gives you a third option.** Every agent declares its data handling practices upfront, in a standard format. Your client checks the declaration before connecting — automatically, no lawyers needed. If it meets your requirements, connect. If not, skip it and move on.

As a result: lower cost (no per-agent data usage negotiations), bigger agent pool (can choose compliant actors through automatic discovery), and automated enforcement of the privacy promises you made to your users.

---

### What about bad actors?

Fair question. ADHP is currently self-declared. An agent could claim Level 3 while logging everything. We're not pretending this is solved — here's how we're thinking about it:

**Phase 1 (now):** Self-declaration. It's how privacy policies work today — you publish what you do and you're legally accountable for it. Not perfect, but it creates a baseline.

**Phase 2:** Operator verification. We verify who runs the agent (KYC). When your identity is known, lying about your data practices has real legal consequences.

**Phase 3:** Automated auditing. Send test data with tracking markers, verify the agent actually does what it claims.

**Phase 4:** Cryptographic guarantees. Hardware-backed processing (TEE/enclaves), signed manifests, proofs of deletion.

We think self-declaration is a reasonable starting point, but we know it's not enough long-term. This is an open question and we'd genuinely appreciate the community's input.

*How should trust verification work? [Join the discussion.](../../discussions)*

---

## The five levels

| Level | Label | In practice |
|-------|-------|-------------|
| 0 | **open** | No promises. Data may be used for anything — training, storage, sharing. |
| 1 | **standard** | No training on your data. Defined retention period. |
| 2 | **sensitive** | No training. Short retention. PII protected. Output sanitized. Third-party sharing only if anonymized. |
| 3 | **strict** | No training, no content logging, no third-party sharing. Strict delegation rules. |
| 4 | **zero-trace** | Memory-only processing. Nothing hits disk. No logs. No delegation. Zero trace. |

If an agent doesn't declare a policy, assume Level 0. Worst case until proven otherwise.

Full definitions in [SPEC.md](SPEC.md#3-data-handling-levels).

---

## Getting started

You only need 4 fields:

```json
{
  "adhp": {
    "level": "standard",
    "training_opt_out": true,
    "max_retention": "30d",
    "third_party_sharing": { "enabled": false }
  }
}
```

That's a valid ADHP declaration. Add more properties when you need them — compliance tags, PII categories, jurisdiction, execution environment. It's all optional beyond these four.

---

## Delegation cascading

This is where it gets interesting. When Agent A delegates to Agent B, the privacy level must meet or exceed what the **caller originally asked for** — not the delegating agent's own level.

```
Caller requests: Level 2 (sensitive)
    |
    v
Agent A (Level 3, strict) -- accepts the job
    |
    |-- delegates to Agent B (Level 2) -- ALLOWED (meets caller's Level 2)
    |-- delegates to Agent C (Level 1) -- BLOCKED (below caller's Level 2)
```

So a Level 3 agent handling a Level 1 request can delegate to Level 1+ agents. The promise is to the caller, not an absolute constraint.

Level 4 agents can't delegate at all — zero-trace means data never leaves the agent boundary, period.

Try it yourself: `python tools/validate_chain.py` — runs through several scenarios.

---

## Properties

**Only 4 are required** — everything else is optional.

### Required

| Property | Type | Description |
|----------|------|-------------|
| `level` | enum | `open`, `standard`, `sensitive`, `strict`, `zero-trace` |
| `training_opt_out` | boolean | Agent commits to NOT using data for model training |
| `max_retention` | enum | `none`, `request`, `session`, `24h`, `7d`, `30d`, `custom`, `unlimited` |
| `third_party_sharing.enabled` | boolean | Whether data is shared with any third party |

### Optional — core

| Property | Type | Description |
|----------|------|-------------|
| `retention_days` | integer | Exact number of days when `max_retention` is `custom` |
| `session_ttl` | string | When retention is `session`, how long that means: `1h`, `4h`, `24h` |
| `content_logging` | boolean | Whether request/response content appears in logs |
| `delegation_policy` | enum | `none`, `same_or_higher`, `unrestricted` |
| `output_sanitization` | boolean | Whether outputs are scrubbed of source data |
| `certification` | string | Future: ID of a verification/audit certificate |

### Optional — privacy & compliance

| Property | Type | Description |
|----------|------|-------------|
| `compliance` | list | Regulatory frameworks: `GDPR`, `HIPAA`, `CCPA`, `POPIA`, `PIPEDA`, `LGPD`, `AI_ACT_EU` |
| `pii_categories` | list | PII types protected: `email`, `phone`, `financial`, `health`, `identity`, `location`, `biometric` |
| `processing_jurisdiction` | list | Where the AI model runs (ISO 3166-1 codes) |
| `storage_jurisdiction` | list | Where data is stored |
| `log_jurisdiction` | list | Where logs are kept |
| `execution_environment` | enum | `standard`, `containerized`, `TEE`, `enclave` |

### Optional — third-party details

| Property | Type | Description |
|----------|------|-------------|
| `third_party_sharing.parties` | list | Declared third parties with type, purpose, and ADHP level if known |
| `third_party_sharing.opt_out_available` | boolean | Whether the data sender can opt out |

Undisclosed third parties are treated as Level 0, it incentivizes transparency as it would increase their traffic.

Full property definitions in [SPEC.md](SPEC.md#4-data-handling-properties).

---

## MCP integration

ADHP fits into the MCP `initialize` handshake as a server capability. Backward-compatible — clients that don't know about ADHP just ignore it.

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": {
      "tools": {},
      "resources": {},
      "adhp": {
        "level": "strict",
        "compliance": ["GDPR"],
        "processing_jurisdiction": ["DE"],
        "pii_categories": ["email", "financial", "health"]
      }
    },
    "serverInfo": {
      "name": "FinanceAnalyzer Pro",
      "version": "1.0.0"
    }
  }
}
```

Client checks the `adhp` capability before sending data. Doesn't meet requirements? Disconnect and find another server. No data is exposed until the client is satisfied.

More: [examples/mcp-handshake.json](examples/mcp-handshake.json)

---

## A2A integration

For [A2A](https://google.github.io/A2A/) agents, ADHP extends the Agent Card:

```json
{
  "name": "FinanceAnalyzer Pro",
  "url": "https://api.finanalyzer.example.com",
  "skills": [
    { "id": "financial-analysis", "name": "Financial Analysis" }
  ],
  "adhp": {
    "level": "strict",
    "compliance": ["GDPR", "AI_ACT_EU"],
    "processing_jurisdiction": ["DE"]
  }
}
```

---

## Try it

Run the delegation chain validator:

```bash
python tools/validate_chain.py
```

It walks through scenarios like:

```
Scenario: Medical data analysis (caller requires: sensitive)
  Agent A (strict) -> Agent B (sensitive) -> Agent C (strict)
  Result: VALID — all agents meet caller's Level 2 minimum

Scenario: Financial report with weak link (caller requires: strict)
  Agent A (strict) -> Agent B (standard) -> Agent C (strict)
  Result: INVALID — Agent B (standard) is below caller's Level 3 minimum
```

Validate a manifest:

```bash
python tools/validate_chain.py --manifest examples/agent-manifest.json
```

---

## Examples

| File | What it shows |
|------|---------------|
| [agent-manifest.json](examples/agent-manifest.json) | Full agent registration with ADHP |
| [mcp-handshake.json](examples/mcp-handshake.json) | ADHP in MCP initialize response |
| [a2a-agent-card.json](examples/a2a-agent-card.json) | ADHP in A2A Agent Card |
| [orchestrator-query.md](examples/orchestrator-query.md) | How an orchestrator discovers agents by trust level |
| [delegation-chain.md](examples/delegation-chain.md) | Delegation cascading scenarios |
| [third-party-sharing.md](examples/third-party-sharing.md) | Third-party sharing rules |

---

## JSON schema

Validate your ADHP manifest:

```bash
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('schemas/adhp-v0.2.schema.json'))
manifest = json.load(open('examples/agent-manifest.json'))
jsonschema.validate(manifest['data_handling'], schema)
print('Valid!')
"
```

---

## Reference implementations

ADHP defines *what* to declare. Here's *how* each level can be achieved:

| Level | One way to do it |
|-------|-----------------|
| 0-1 | Standard server with logging config |
| 2 | PII tokenization proxy (Skyflow, Piiano) between client and server |
| 3 | Output guard (LlamaGuard) validates no source data leaks |
| 4 | Trusted Execution Environment (AWS Nitro, Intel SGX) with memory-only processing |

These are suggestions. Operators choose their own approach as long as the declared level is met.

---

## How ADHP relates to existing standards

| Standard | Their focus | What ADHP adds |
|----------|-----------|----------------|
| GDPR | Legal framework for personal data (EU) | Makes GDPR-relevant practices machine-queryable |
| HIPAA | Health data protection (US) | Agents declare health PII handling, orchestrators filter by compliance |
| ISO 27001 | Organizational security controls | ADHP works at the agent level, not the org level |
| SOC 2 | Trust service criteria | ADHP is real-time and per-request; SOC 2 is periodic |
| MCP | Agent-tool communication | ADHP adds data handling metadata to the capability handshake |
| A2A | Agent-to-agent communication | ADHP enriches Agent Cards with trust info |
| OAuth/OIDC | Authentication and authorization | ADHP is about what happens *after* auth succeeds |

---

## Status

**Version:** 0.2.0 (Draft)
**License:** Apache 2.0

This is a draft looking for feedback. Not an official standard or MCP extension (yet).

**What's next:**
1. Community feedback on the spec (you're here)
2. Reference implementation in [Agent Registry](https://github.com/StevenJohnson998/agent-registry)
3. Propose as MCP extension via the SEP process
4. Seek AAIF adoption

---

## Contributing

We're looking for feedback on:

- Are the five levels right? Too many? Too few?
- Is the delegation cascading rule practical?
- What data handling concerns are we missing?
- How should verification work?
- How does this interact with AI regulation in your jurisdiction?

**How to contribute:**
- Open a [Discussion](../../discussions) for questions and ideas
- Open an [Issue](../../issues) for problems or suggestions
- Submit a PR for spec changes (open an issue first)
- All contributors agree to the [Contributor License Agreement](CLA.md)

---

## License

[Apache 2.0](LICENSE) — see [CLA.md](CLA.md) for contributor terms.
