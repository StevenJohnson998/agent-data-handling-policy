# Agent Data Handling Policy (ADHP)

[![ADHP Validator](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml/badge.svg)](https://github.com/StevenJohnson998/agent-data-handling-policy/actions/workflows/validate.yml)

**A privacy label for AI agents.**

When an AI agent processes your data, what happens to it? Does it get stored? Used for training? Forwarded to a third party? Logged? Today, there's no standard way to know.

ADHP is an open specification that lets AI agents declare their data handling practices in a machine-readable format. Think of it as GDPR's Article 13 (transparency) but designed for agent-to-agent communication.

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

An orchestrator reads this and knows: *this agent won't train on my data, deletes it after each request, complies with GDPR and HIPAA, protects email/financial/health data, processes in Germany, and doesn't share with anyone.*

### Minimal Declaration

Only 4 fields are required to get started:

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

That's it. Add more properties as you need them. [See all properties below.](#properties)

---

## Why This Matters

AI agents are multiplying. MCP has 97M+ monthly SDK downloads. Google's A2A protocol connects agents to agents. But none of these protocols answer a basic question: **what does this agent do with my data?**

This matters because:

- **An orchestrator choosing between 50 agents** has no standard way to compare their privacy practices
- **A healthcare company** can't programmatically verify that an agent won't train on patient data
- **When Agent A delegates to Agent B**, there's no way to verify the privacy chain holds
- **Compliance teams** can't audit agent data flows without manual review of each provider

ADHP solves this with five simple levels and a set of detailed properties.

---

## Why It Also Matters for Service Providers

ADHP isn't just for consumers of agents. **If you operate an AI service, you need it too.**

Your service has a privacy policy. Your users consented to specific data handling terms. But the moment your service connects to an external MCP server, you inherit that server's data practices -- and you may have no idea what they are.

**Today, providers face two bad options:**

**Option A: Only use trusted agents.** You manually vet each agent provider. You negotiate data handling agreements, review contracts, involve legal. This is slow, expensive, and limits you to a handful of pre-approved agents. Your pool of usable agents shrinks to whoever you've had time to negotiate with.

**Option B: Use agents without vetting.** You move fast and connect to whatever MCP server gets the job done. But you have no idea what it does with your users' data. If that server trains on content, logs everything, or forwards data to third parties, **you just breached your own privacy policy** -- and potentially violated GDPR Article 28 (processor obligations), HIPAA BAA requirements, or your local data protection regulations.

**ADHP gives you a third option:**

Every agent declares its data handling practices in a standard, machine-readable format. Your client checks the ADHP level before connecting. If it meets your requirements, connect instantly -- no negotiation, no legal review, no contracts. If it doesn't meet your requirements, skip it automatically.

This means:
- **Lower cost.** No need to negotiate data handling agreements one by one -- the policy is embedded in the protocol.
- **Larger agent pool.** Instead of a curated shortlist, every agent with adequate data protection is available to you.
- **Automated compliance.** Your system enforces your privacy promises programmatically, not through manual review.
- **Audit trail.** Document the ADHP levels of every service in your chain for compliance audits.

---

### What About Bad Actors?

ADHP is currently **self-declared**. An agent could claim Level 3 (strict) while actually logging everything. This is a real concern, and we address it progressively:

- **Phase 1 (now):** Self-declaration. Similar to how websites publish privacy policies today -- it creates accountability and a basis for legal action if violated, but relies on trust.
- **Phase 2:** Operator verification (KYC). We verify who operates the agent. A verified identity creates legal accountability -- lying about your data handling practices when your identity is known has real consequences.
- **Phase 3:** Automated auditing. Auditor agents send test data with tracking markers and verify that declared policies match actual behavior.
- **Phase 4:** Cryptographic verification. Hardware-backed guarantees (TEE/enclaves), signed manifests (W3C Verifiable Credentials), and cryptographic proofs of deletion.

**We believe self-declaration is a meaningful first step** -- it's how GDPR compliance works today (organizations declare their practices and are held accountable). But we recognize this is an open question, and we'd love the community's input on how to make verification practical and trustworthy.

*How should trust verification work? [Join the discussion.](../../discussions)*

---

## The Five Levels

| Level | Label | What It Means |
|-------|-------|---------------|
| 0 | **open** | No promises. Data may be used for anything including training, stored indefinitely, shared freely. |
| 1 | **standard** | No training on your data. Defined retention period. |
| 2 | **sensitive** | No training. Short retention. PII is protected. Output is sanitized. Third-party sharing only if anonymized. |
| 3 | **strict** | No training, no content logging, no third-party sharing. Delegation only to same level or above. |
| 4 | **zero-trace** | Memory-only processing. Nothing written to disk. No logs. No delegation. Data leaves no trace. |

If an agent doesn't declare a policy, **assume Level 0** (the worst case). This incentivizes transparency.

Full definitions: [SPEC.md, Section 3](SPEC.md#3-data-handling-levels)

---

## Delegation Cascading

The key innovation. When Agent A delegates to Agent B, the privacy level at the destination must meet or exceed what the **caller originally requested** -- not just the delegating agent's own level.

```
Caller requests: Level 2 (sensitive)
    |
    v
Agent A (Level 3, strict) -- accepts the job
    |
    |-- delegates subtask to Agent B (Level 2) -- ALLOWED (meets caller's Level 2)
    |-- delegates subtask to Agent C (Level 1) -- BLOCKED (below caller's Level 2)
```

This means a Level 4 agent handling a Level 1 request can delegate to Level 1+ agents. The promise is to the **caller**, not an absolute constraint.

Level 4 agents cannot delegate at all, regardless of the caller's request level, because zero-trace means data never leaves the agent boundary.

Try it: `python tools/validate_chain.py` ([see below](#try-it))

---

## Properties

Beyond the level, agents declare specific properties. **Only 4 are required** -- everything else is optional and can be added incrementally.

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `level` | enum | `open`, `standard`, `sensitive`, `strict`, `zero-trace` |
| `training_opt_out` | boolean | Agent commits to NOT using data for model training |
| `max_retention` | enum | `none`, `request`, `session`, `24h`, `7d`, `30d`, `custom`, `unlimited` |
| `third_party_sharing.enabled` | boolean | Whether data is shared with any third party |

### Optional — Core

| Property | Type | Description |
|----------|------|-------------|
| `retention_days` | integer | Exact number of days when `max_retention` is `custom` |
| `session_ttl` | string | When retention is `session`, how long that means: `1h`, `4h`, `24h` |
| `content_logging` | boolean | Whether request/response content appears in logs |
| `delegation_policy` | enum | `none`, `same_or_higher`, `unrestricted` |
| `output_sanitization` | boolean | Whether outputs are scrubbed of source data |
| `certification` | string | Future: ID of a verification/audit certificate |

### Optional — Privacy & Compliance

| Property | Type | Description |
|----------|------|-------------|
| `compliance` | list | Regulatory frameworks: `GDPR`, `HIPAA`, `CCPA`, `POPIA`, `PIPEDA`, `LGPD`, `AI_ACT_EU`, etc. |
| `pii_categories` | list | PII types protected: `email`, `phone`, `financial`, `health`, `identity`, `location`, `biometric` |
| `processing_jurisdiction` | list | Where the AI model runs (ISO 3166-1 codes) |
| `storage_jurisdiction` | list | Where data is stored |
| `log_jurisdiction` | list | Where logs are kept |
| `execution_environment` | enum | `standard`, `containerized`, `TEE`, `enclave` |

### Optional — Third-Party Details

| Property | Type | Description |
|----------|------|-------------|
| `third_party_sharing.parties` | list | Declared third parties with type, purpose, and ADHP level if known |
| `third_party_sharing.opt_out_available` | boolean | Whether the data sender can opt out of sharing |

If a third party is undisclosed, it is treated as Level 0 (assume the worst).

Full property definitions: [SPEC.md, Section 4](SPEC.md#4-data-handling-properties)

---

## MCP Integration

ADHP is designed to complement [MCP (Model Context Protocol)](https://modelcontextprotocol.io/). During the MCP `initialize` handshake, a server can declare its ADHP policy as a capability:

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

The MCP client checks: does this server meet my requirements? If not, disconnect and find another server. No data is sent until the client is satisfied with the ADHP declaration.

See: [examples/mcp-handshake.json](examples/mcp-handshake.json)

---

## A2A Integration

For [A2A (Agent-to-Agent)](https://google.github.io/A2A/) agents, ADHP extends the Agent Card:

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

## Try It

### Validate a delegation chain

```bash
python tools/validate_chain.py
```

This runs example scenarios showing how delegation cascading works:

```
Scenario: Medical data analysis (caller requires: sensitive)
  Agent A (strict) -> Agent B (sensitive) -> Agent C (strict)
  Result: VALID -- all agents meet caller's Level 2 minimum

Scenario: Financial report with weak link (caller requires: strict)
  Agent A (strict) -> Agent B (standard) -> Agent C (strict)
  Result: INVALID -- Agent B (standard) is below caller's Level 3 minimum
```

### Validate a manifest

```bash
python tools/validate_chain.py --manifest examples/agent-manifest.json
```

---

## Examples

| File | Description |
|------|-------------|
| [agent-manifest.json](examples/agent-manifest.json) | Complete agent registration with ADHP |
| [mcp-handshake.json](examples/mcp-handshake.json) | ADHP in MCP initialize response |
| [a2a-agent-card.json](examples/a2a-agent-card.json) | ADHP in A2A Agent Card |
| [orchestrator-query.md](examples/orchestrator-query.md) | How an orchestrator discovers agents by trust |
| [delegation-chain.md](examples/delegation-chain.md) | Delegation cascading scenarios explained |
| [third-party-sharing.md](examples/third-party-sharing.md) | Third-party sharing rules and examples |

---

## JSON Schema

Validate your ADHP manifest against the schema:

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

## Reference Implementation Patterns

ADHP defines *what* agents must declare. Here's *how* each level can be achieved in practice:

| Level | Implementation Pattern |
|-------|----------------------|
| Level 0-1 | Standard server with logging configuration |
| Level 2 | PII tokenization proxy (e.g., Skyflow MCP Gateway) between client and server |
| Level 3 | Output guard (e.g., LlamaGuard as MCP server) validates no source data leaks |
| Level 4 | Trusted Execution Environment (AWS Nitro Enclaves, Intel SGX) with memory-only processing |

These are suggestions, not requirements. Operators choose their own implementation as long as the declared level is met.

---

## Relationship to Other Standards

| Standard | Focus | How ADHP Complements It |
|----------|-------|------------------------|
| GDPR | Legal framework for personal data (EU) | ADHP makes GDPR-relevant practices machine-queryable |
| HIPAA | Health data protection (US) | Agents declare health PII handling; orchestrators filter by HIPAA compliance |
| ISO 27001 | Organizational security controls | ADHP operates at the agent level, not the organization level |
| SOC 2 | Trust service criteria | ADHP is real-time and per-request; SOC 2 is periodic audit |
| MCP | Protocol for agent-tool communication | ADHP adds data handling metadata to the capability handshake |
| A2A | Protocol for agent-to-agent communication | ADHP enriches Agent Cards with trust information |
| OAuth/OIDC | Authentication and authorization | ADHP is about data handling *after* auth succeeds |

---

## Project Status

**Version:** 0.2.0 (Draft)
**License:** Apache 2.0

This specification is a draft seeking community feedback. It is not yet an official standard or MCP extension.

**Roadmap:**
1. Community feedback on the spec (current)
2. Reference implementation in [Agent Registry](https://github.com/StevenJohnson998/agent-registry)
3. Propose as MCP Extension (via SEP process)
4. Seek AAIF adoption

---

## Contributing

This specification needs your input. We're particularly looking for feedback on:

- Are the five levels right? Too many? Too few?
- Is the delegation cascading rule practical?
- What data handling concerns are we missing?
- How should verification work?
- How does this interact with AI regulation in your jurisdiction?

**How to contribute:**
- Open a [Discussion](../../discussions) for questions and ideas
- Open an [Issue](../../issues) for specific problems or suggestions
- Submit a PR for spec changes (please open an issue first)
- All contributors must agree to the [Contributor License Agreement](CLA.md)

---

## License

[Apache 2.0](LICENSE) -- see [CLA.md](CLA.md) for contributor terms.
