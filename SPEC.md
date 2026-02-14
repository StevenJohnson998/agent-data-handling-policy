# Agent Data Handling Policy (ADHP) Specification

> **Version:** 0.2.0 (Draft)
> **Status:** RFC — Request for Comments
> **Author:** Steven Johnson / ADHP Project
> **Date:** February 2026
> **License:** Apache 2.0
> **Repository:** [github.com/StevenJohnson998/agent-data-handling-policy](https://github.com/StevenJohnson998/agent-data-handling-policy)

---

## 1. Purpose

When an AI agent processes your data, what happens to it? Is it stored? Used for training? Forwarded to another service? Processed in a different country?

Traditional security frameworks (ISO 27001, GDPR) focus on *who can access data*. ADHP addresses a different question — one that becomes critical in a world of autonomous AI agents: **what does the agent do with the data during and after processing?**

This specification defines a standardized, machine-readable way for AI agents to declare their data handling practices. It enables orchestrators, gateways, and registries to make informed decisions **before any data is sent** — based on the sensitivity of the data and the regulatory context.

ADHP is designed as a **privacy passport for AI agents** — a cross-cutting transparency layer that extends [MCP](https://modelcontextprotocol.io) (Anthropic) and [A2A](https://google.github.io/A2A) (Google).

---

## 2. Problem Statement

Consider a recruiting scenario: an AI agent is asked to find candidates. It delegates to a background check agent, which calls a credit score agent, which calls an identity verification agent. At each step, increasingly sensitive data is passed along — CVs, employment history, social security numbers, biometric data.

At every link in this chain, the same questions arise:

- Will the agent use the data to train or improve its model?
- Will it store the data after returning results?
- Will it log the contents of the request?
- Will it forward the data to a sub-agent?
- Will its response contain the original sensitive data?
- Will it share data with third parties?
- Where physically is the data being processed?

Today, there is no standard way for agents to declare this information, and no standard way for clients to filter agents based on these criteria.

Under GDPR, the data controller is accountable for every sub-processor in the chain ([Art. 28](https://gdpr-info.eu/art-28-gdpr/)). Without visibility into agent data handling, demonstrating compliance becomes practically impossible.

---

## 3. Data Handling Levels

ADHP defines five levels of data handling, from most permissive to most restrictive.

### 3.1 Summary Table

| Level | Label | Training | Persistence | Logging | Delegation | Output | Third-Party Sharing |
|-------|-------|----------|-------------|---------|------------|--------|---------------------|
| 0 | **open** | Yes | Unlimited | Full | Unrestricted | May contain source data | Allowed |
| 1 | **standard** | No | Session-based | Metadata only | Same level required | May contain derived data | With consent |
| 2 | **sensitive** | No | Request only | Metadata only | Same level+, must be declared | Sanitized — no source data | Anonymized only |
| 3 | **strict** | No | Request only | No content logging | Same level+ only | Sanitized + reviewed | Not allowed |
| 4 | **zero-trace** | No | None (streaming only) | None | No delegation | Sanitized, no data leaves agent | Not allowed |

### 3.2 Detailed Definitions

#### Level 0 — Open

The agent makes no guarantees about data handling. Data may be used for any purpose including model training, indefinite storage, and redistribution.

**This is the default assumption when an agent does not declare a policy.** Undeclared agents are treated as Level 0 everywhere ADHP is checked — in registries, gateways, and delegation chains. This incentivizes agents to declare their practices explicitly.

**Use case:** Public data processing, open-source analysis, non-sensitive content generation.

#### Level 1 — Standard

The agent will not use the data for model training. Data is retained for the duration of the session and then deleted. Only metadata (timestamps, request IDs, token counts) is logged — not the content itself. The agent may delegate to sub-agents, but only those that also operate at Standard level or above.

**Use case:** General business operations, non-regulated internal data, standard API calls.

#### Level 2 — Sensitive

Same protections as Standard, with additional constraints: data is retained only for the duration of a single request (not the full session). If the agent delegates to sub-agents, this must be explicitly declared in the agent's manifest. The agent's output is sanitized — it will not contain verbatim source data.

**Use case:** Personal data processing (GDPR Art. 6), financial analysis, HR data, customer records.

#### Level 3 — Strict

The agent provides strong confidentiality guarantees. No content logging of any kind. Data is retained only during request processing. Delegation is only permitted to agents at the same level or higher. Output is sanitized and reviewed (automated or manual) to prevent data leakage. No third-party sharing of any kind.

**Use case:** Legal documents, trade secrets, medical records (HIPAA), classified business strategies.

#### Level 4 — Zero-Trace

The highest level of confidentiality. The agent processes data in memory only — no disk writes at any point. No logging whatsoever. No delegation to any other agent. Output is sanitized and constrained so that no source data leaves the agent boundary. This level is designed for data that must leave absolutely no trace.

**Use case:** National security, pre-announcement M&A data, whistleblower submissions, highly sensitive IP.

> **Honest assessment:** Levels 3 and 4 make strong promises that are difficult to verify without runtime enforcement (containerization, TEE). Today, these levels represent commitments — not proofs. The [verification roadmap](#7-verification-roadmap) describes how ADHP progressively builds from trust-based declarations toward cryptographic guarantees.

---

## 4. Data Handling Properties

Beyond the overall level, each agent declares specific properties in its manifest. These properties give clients granular control over what they accept.

### 4.1 Core Properties

| Property | Type | Description |
|----------|------|-------------|
| `level` | enum | One of: `open`, `standard`, `sensitive`, `strict`, `zero-trace` |
| `training_opt_out` | boolean | Whether the agent commits to NOT using data for model training |
| `max_retention` | enum | How long data is kept: `none`, `request`, `session`, `24h`, `7d`, `30d`, `custom`, `unlimited` |
| `retention_days` | integer | Exact number of days when `max_retention` is `custom` |
| `session_ttl` | string | When retention is `session`, how long that means: `1h`, `4h`, `24h` |
| `content_logging_opt_out` | boolean | Whether the agent commits to NOT logging request/response content |
| `delegation_policy` | enum | Sub-agent policy: `none`, `same_or_higher`, `unrestricted` |
| `delegation_depth` | integer (optional) | Maximum depth of delegation chain allowed |
| `output_sanitization_opt_in` | boolean | Whether the agent commits to scrubbing outputs of source data |
| `certification` | string (nullable) | Future: ID of a verification/audit certificate |

### 4.2 Privacy & Compliance Properties

| Property | Type | Description |
|----------|------|-------------|
| `compliance` | list[string] | Regulatory frameworks: `GDPR`, `HIPAA`, `CCPA`, `POPIA`, `PIPEDA`, `LGPD`, `AI_ACT_EU`, etc. |
| `pii_categories` | list[string] | PII types protected: `email`, `phone`, `financial`, `health`, `identity`, `location`, `biometric` |
| `processing_jurisdiction` | list[string] | Where the AI model runs (ISO 3166-1 country codes) |
| `storage_jurisdiction` | list[string] | Where data is stored (ISO 3166-1 country codes) |
| `log_jurisdiction` | list[string] | Where logs are kept (ISO 3166-1 country codes) |
| `execution_environment` | enum | `standard`, `containerized`, `TEE`, `enclave` |

> **Important note on `compliance`:** Declaring `compliance: ["GDPR"]` means the agent operator claims their processing activities are designed to support GDPR compliance. It does NOT mean the agent is "GDPR certified" — no such certification exists. Compliance depends on the specific processing activity, the legal basis, and the contractual chain (DPAs). ADHP is a transparency tool, not a compliance certification. See [Discussion #7](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/7) for planned evolution of this field.

### 4.3 Third-Party Sharing Properties

| Property | Type | Description |
|----------|------|-------------|
| `third_party_opt_out` | boolean | Whether the agent commits to NOT sharing data with third parties |
| `third_party_sharing.enabled` | boolean | Detailed: whether data is shared with any third party |
| `third_party_sharing.purpose` | list[enum] | Why data is shared: `analytics`, `advertising`, `improvement`, `subprocessing`, `resale` |
| `third_party_sharing.sanitized` | boolean | Whether shared data is anonymized/stripped of PII |
| `third_party_sharing.parties` | list[object] | Declared third parties with type, purpose, and ADHP level if known |
| `third_party_sharing.parties_disclosed` | boolean | Whether the list of third parties is publicly available |
| `third_party_sharing.opt_out_available` | boolean | Whether the data sender can opt out of sharing |

If a third party is undisclosed, it is treated as Level 0 (assume the worst).

### 4.4 Naming Convention — Opt-out/Opt-in Pattern

All boolean fields follow a consistent principle: **undeclared = assume the worst**.

- `training_opt_out: true` → the agent commits to NOT training on data
- `content_logging_opt_out: true` → the agent commits to NOT logging content
- `output_sanitization_opt_in: true` → the agent commits to scrubbing outputs
- If a field is not declared, assume the agent does NOT protect.

This "fail-closed" design means agents must actively declare their protections. Silence is treated as absence of protection.

### 4.5 Example Manifest

```json
{
  "agent_name": "FinanceAnalyzer Pro",
  "data_handling": {
    "level": "strict",
    "training_opt_out": true,
    "max_retention": "request",
    "delegation_policy": "same_or_higher",
    "compliance": ["GDPR", "AI_ACT_EU"],
    "pii_categories": ["email", "financial"],
    "processing_jurisdiction": ["DE", "FR"],
    "storage_jurisdiction": ["DE"],
    "execution_environment": "containerized",
    "certification": null,
    "third_party_sharing": {
      "enabled": false,
      "purpose": [],
      "sanitized": false,
      "parties": [],
      "parties_disclosed": true,
      "opt_out_available": false
    }
  }
}
```

---

## 5. Delegation Cascading Rule

When Agent A delegates work to Agent B, the data handling level must be maintained or strengthened — **never weakened**.

The rule is based on the **caller's original request level**, not the delegating agent's own level. A Level 3 agent handling a Level 1 request can delegate to any Level 1+ agent.

Level 4 (zero-trace) cannot delegate at all — data never leaves the agent boundary.

```
User requests: Level 2 (sensitive)
    |
    v
Agent A (Level 3, strict) — accepts the job
    |
    |— delegates to Agent B (Level 2) — ✅ ALLOWED (meets caller's Level 2)
    |— delegates to Agent C (Level 1) — ❌ BLOCKED (below caller's Level 2)
```

Gateways can raise requirements but never lower them. If the user requires Level 2 and the gateway requires Level 3, Level 3 applies.

Enforcement of this rule can happen at multiple points — see [Section 11](#11-enforcement-architecture).

---

## 6. Third-Party Sharing Matrix

| Level | Sharing Allowed | Conditions |
|-------|----------------|------------|
| open | Yes | No restrictions |
| standard | Yes | Only with sender's consent |
| sensitive | Limited | Only anonymized/sanitized data |
| strict | No | Third-party sharing prohibited |
| zero-trace | No | Third-party sharing prohibited, no data leaves agent |

---

## 7. Verification Roadmap

ADHP starts with trust-based declarations and progressively builds toward cryptographic guarantees. Each phase raises the cost of non-compliance.

### Phase 1 — Self-Declaration (v0.2 — current)
Agents declare their own data handling level. Registries store these declarations. Gateways and clients filter based on declared levels. **Trust is based on the agent operator's reputation.**

### Phase 2 — Verified Badge
Agent operators can request verification:
- KYC (Know Your Customer) for the operating organization
- Technical audit of the agent's data handling practices
- Periodic re-verification
- A "Verified" badge displayed in the registry

### Phase 3 — Automated Auditing
Trusted "Auditor" agents periodically test registered agents by:
- Sending test data with tracking markers (canary data)
- Verifying the data is handled according to the declared policy
- Checking that delegation chains maintain confidentiality levels
- Reporting violations automatically

### Phase 4 — Cryptographic Verification
Technical enforcement through:
- Encrypted data envelopes that enforce retention policies
- Cryptographic proofs of deletion
- Secure enclaves for zero-trace processing (TEE attestation)
- Signed source code verification for open-source agents
- Zero-knowledge proofs of compliance
- Audit trails for verification history

These mechanisms raise the cost of violations significantly, though no single mechanism provides absolute guarantees. For a detailed analysis of what each approach can and cannot prevent, see the [enforcement patterns discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5).

---

## 8. Protocol Integration

### 8.1 MCP Integration

ADHP adds an `adhp` key inside MCP's `capabilities` object during the `initialize` handshake. The client reads this before sending any data.

See [examples/mcp-handshake.json](examples/mcp-handshake.json) for a complete example.

### 8.2 A2A Integration

ADHP enriches A2A Agent Cards with data handling metadata, enabling trust-based agent discovery.

See [examples/a2a-agent-card.json](examples/a2a-agent-card.json) for a complete example.

### 8.3 Registry Integration

Registries can store ADHP metadata alongside agent capabilities, enabling filtered discovery:

```
GET /agents?min_data_handling_level=sensitive&jurisdiction=EU&third_party_sharing=false
```

Returns only agents that meet or exceed the requested data handling requirements.

---

## 9. Default Behavior

- If an agent does not declare a `data_handling` policy, it defaults to `level: "open"` — **assume the worst case if not declared.**
- This applies everywhere ADHP is checked: in registries, gateways, and delegation chains. An agent in a chain that does not implement ADHP is treated as having no data policy.
- This incentivizes agents to explicitly declare their policy, as undeclared agents will be filtered out of any privacy-sensitive workflow.

### 9.1 Jurisdiction Checking

Server jurisdiction fields (`processing_jurisdiction`, `storage_jurisdiction`) declare where data **may** be processed or stored. A client's accepted jurisdictions define where data is **allowed** to go.

**Checking rule:** All server-declared jurisdictions must be within the client's accepted list. If a server declares `["DE", "US"]` and a client accepts `["DE"]`, the check fails — the server may process in the US, which is outside the accepted list.

**Undeclared jurisdictions:** If a server does not declare any jurisdiction, assume worst case — the check fails for any client that has jurisdiction requirements.

**Gateways:** A gateway can enforce stricter jurisdiction requirements than the client. The highest requirement (most restrictive accepted list) applies — gateways can raise requirements but never lower them.

> **v0.3 planned:** Introduce `guaranteed` vs. `possible` jurisdiction declarations for multi-region providers. See [Discussion #7](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/7).

> **v0.4 planned:** Cryptographic DPA verification — runtime proof that valid Data Processing Agreements exist between parties in the delegation chain. See [Discussion #8](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/8).

---

## 10. Relationship to Other Standards

ADHP is designed to **complement, not replace**, existing standards. It provides the machine-readable transparency layer that these frameworks require but currently lack tooling for.

| Standard | Focus | How ADHP Complements |
|----------|-------|---------------------|
| **GDPR** | Legal framework for personal data in the EU | Technical declaration of compliance-relevant practices across agent chains |
| **HIPAA** | Health data protection (US) | Agents declare health PII handling; clients filter by HIPAA compliance |
| **EU AI Act** | AI system regulation (EU) | Machine-readable transparency for Article 50 obligations |
| **CCPA** | Consumer privacy (US) | Third-party sharing declarations, verifiable at runtime |
| **ISO 27001** | Who can access data within an organization | What happens to data after an agent processes it |
| **SOC 2** | Organizational security controls | Agent-level data handling transparency |
| **MCP** | Protocol for agent-tool communication (Anthropic) | ADHP adds data handling metadata to the capability handshake |
| **A2A** | Protocol for agent-to-agent communication (Google) | ADHP enriches Agent Cards with trust information |
| **MCP Gateways** | Policy enforcement, auth, routing | ADHP gives gateways a standardized language for data handling enforcement |
| **OAuth/OIDC** | Who is authorized to call the agent | Authorization is separate — ADHP covers data handling *after* auth succeeds |

> ⚠️ An agent operating at "strict" level within the EU would still need to comply with GDPR independently. ADHP makes the agent's practices transparent and machine-queryable — it does not replace legal due diligence.

---

## 11. Enforcement Architecture

ADHP is declarative — it defines what agents promise. Enforcement is a separate concern that operates at multiple points:

| Layer | What it does | Example |
|-------|-------------|---------|
| **Protocol** | ADHP declared in MCP handshake / A2A Agent Cards | Client checks before sending data |
| **Gateway** | Reads ADHP, blocks non-compliant connections | Organizational policy enforcement, audit trails |
| **Registry** | Filters agents at discovery time by ADHP metadata | Trust-based discovery, KYC verification |
| **Runtime** | Containers/TEEs constrain what agents can physically do | Backs up Level 3-4 declarations with infrastructure |
| **Cryptographic** | Signed code, encrypted envelopes, TEE attestation | Mathematically proven compliance (Phase 4) |

These layers are complementary. Each raises the cost of non-compliance. Combined, they make violations expensive, detectable, and attributable. No single layer is sufficient on its own.

For implementation patterns at each layer, see the [enforcement patterns discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5). For architectural rationale, see the [architecture discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6).

---

## Contributing

This specification is a draft. We welcome feedback on:
- Are the five levels sufficient? Too many? Too few?
- Are there data handling concerns we've missed?
- How should verification work in practice?
- How does this interact with emerging AI regulation?

Please open a [Discussion](../../discussions) for ideas, an [Issue](../../issues) for bugs, or submit a PR.
