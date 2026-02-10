# Agent Data Handling Policy (ADHP) Specification

> **Version:** 0.2.0 (Draft)
> **Status:** RFC — Request for Comments
> **Author:** Agent Registry Project
> **Date:** February 2026

## 1. Purpose

In a multi-agent ecosystem, when an orchestrator sends data to an agent for processing, the sender needs to know: **what will happen to my data?**

Traditional security frameworks (ISO 27001, GDPR) focus on *who can access data*. The Agent Data Handling Policy (ADHP) addresses a different question specific to the agentic world: **what does the agent do with the data during and after processing?**

This specification defines a standardized way for AI agents to declare their data handling practices, enabling orchestrators to make informed routing decisions based on the sensitivity of the data being processed.

---

## 2. Problem Statement

When Agent A sends a financial document to Agent B for analysis:

- Will Agent B use that document to train or improve its model?
- Will Agent B store the document after returning the analysis?
- Will Agent B log the contents of the document?
- Will Agent B forward the document to a sub-agent (Agent C)?
- Will Agent B's response contain the original sensitive data?
- Will Agent B share the data with third parties?
- Where physically is Agent B processing the data?

Today, there is no standard way for agents to declare this information, and no standard way for orchestrators to filter agents based on these criteria.

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

The agent makes no guarantees about data handling. Data may be used for any purpose including model training, indefinite storage, and redistribution. This is the default assumption when an agent does not declare a policy.

**Use case:** Public data processing, open-source analysis, non-sensitive content generation.

#### Level 1 — Standard

The agent will not use the data for model training. Data is retained for the duration of the session and then deleted. Only metadata (timestamps, request IDs, token counts) is logged — not the content itself. The agent may delegate to sub-agents, but only those that also operate at Standard level or above.

**Use case:** General business operations, non-regulated internal data, standard API calls.

#### Level 2 — Sensitive

Same protections as Standard, with additional constraints: data is retained only for the duration of a single request (not the full session). If the agent delegates to sub-agents, this must be explicitly declared in the agent's manifest. The agent's output is sanitized — it will not contain verbatim source data.

**Use case:** Personal data processing, financial analysis, HR data, customer records.

#### Level 3 — Strict

The agent provides strong confidentiality guarantees. No content logging of any kind. Data is retained only during request processing. Delegation is only permitted to agents at the same level or higher. Output is sanitized and reviewed (automated or manual) to prevent data leakage. No third-party sharing of any kind.

**Use case:** Legal documents, trade secrets, medical records, classified business strategies.

#### Level 4 — Zero-Trace

The highest level of confidentiality. The agent processes data in memory only — no disk writes at any point. No logging whatsoever. No delegation to any other agent. Output is sanitized and constrained so that no source data leaves the agent boundary. This level is designed for data that must leave absolutely no trace.

**Use case:** National security, pre-announcement M&A data, whistleblower submissions, highly sensitive IP.

---

## 4. Data Handling Properties

Beyond the overall level, each agent declares specific properties in its manifest:

### 4.1 Core Properties

| Property | Type | Description |
|----------|------|-------------|
| `level` | enum | One of: `open`, `standard`, `sensitive`, `strict`, `zero-trace` |
| `training_opt_out` | boolean | Whether the agent commits to NOT using data for model training |
| `max_retention` | enum | How long data is kept: `none`, `request`, `session`, `24h`, `7d`, `30d`, `custom`, `unlimited` |
| `retention_days` | integer | Exact number of days when `max_retention` is `custom` |
| `session_ttl` | string | When retention is `session`, how long that means: `1h`, `4h`, `24h` |
| `content_logging` | boolean | Whether the content of requests/responses appears in logs |
| `delegation_policy` | enum | Sub-agent policy: `none`, `same_or_higher`, `unrestricted` |
| `output_sanitization` | boolean | Whether outputs are scrubbed of source data |
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

### 4.3 Third-Party Sharing Properties

| Property | Type | Description |
|----------|------|-------------|
| `third_party_sharing.enabled` | boolean | Whether data is shared with any third party |
| `third_party_sharing.purpose` | list[enum] | Why data is shared: `analytics`, `advertising`, `improvement`, `subprocessing`, `resale` |
| `third_party_sharing.sanitized` | boolean | Whether shared data is anonymized/stripped of PII |
| `third_party_sharing.parties` | list[object] | Declared third parties with type, purpose, and ADHP level if known |
| `third_party_sharing.parties_disclosed` | boolean | Whether the list of third parties is publicly available |
| `third_party_sharing.opt_out_available` | boolean | Whether the data sender can opt out of sharing |

If a third party is undisclosed, it is treated as Level 0 (assume the worst).

### 4.4 Example Manifest

```json
{
  "agent_name": "FinanceAnalyzer Pro",
  "data_handling": {
    "level": "strict",
    "training_opt_out": true,
    "max_retention": "request",
    "content_logging": false,
    "delegation_policy": "same_or_higher",
    "output_sanitization": true,
    "compliance": ["GDPR", "AI_ACT_EU"],
    "pii_categories": ["email", "financial"],
    "processing_jurisdiction": ["DE", "FR"],
    "storage_jurisdiction": ["DE"],
    "log_jurisdiction": ["DE"],
    "execution_environment": "containerized",
    "certification": null,
    "third_party_sharing": {
      "enabled": false,
      "purpose": [],
      "sanitized": true,
      "parties": [],
      "parties_disclosed": true,
      "opt_out_available": true
    }
  }
}
```

---

## 5. Delegation Cascading Rule

**Critical principle:** When Agent A delegates work to Agent B, the data handling level must be maintained or strengthened — never weakened.

| Agent A Level | Agent B Minimum Level |
|---------------|----------------------|
| open | open (any) |
| standard | standard |
| sensitive | sensitive |
| strict | strict |
| zero-trace | No delegation allowed |

The delegation rule is based on the **caller's original request level**, not the delegating agent's own level. A Level 3 agent handling a Level 1 request can delegate to any Level 1+ agent.

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

### Phase 1 — Self-Declaration (MVP)
Agents declare their own data handling level. The registry stores this declaration. Orchestrators filter based on declared levels. **Trust is based on the agent operator's reputation.**

### Phase 2 — Verified Badge
Agent operators can request verification. This involves:
- KYC (Know Your Customer) for the operating organization
- Technical audit of the agent's data handling practices
- Periodic re-verification
- A "Verified" badge displayed in the registry

### Phase 3 — Automated Auditing
Trusted "Auditor" agents periodically test registered agents by:
- Sending test data with tracking markers
- Verifying the data is handled according to the declared policy
- Checking that delegation chains maintain confidentiality levels
- Reporting violations automatically

### Phase 4 — Cryptographic Verification
Technical enforcement through:
- Encrypted data envelopes that enforce retention policies
- Cryptographic proofs of deletion
- Secure enclaves for zero-trace processing (TEE attestation)
- Audit trails for verification history

These mechanisms raise the cost of violations significantly, though no single mechanism provides absolute guarantees. For a detailed analysis of what each approach can and cannot prevent, see the [enforcement patterns discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5).

---

## 8. API Integration

### Registering an Agent with Data Handling Policy

```
POST /agents
{
  "name": "FinanceAnalyzer Pro",
  "description": "Advanced financial document analysis",
  "capabilities": ["financial-analysis", "document-parsing"],
  "endpoint": "https://api.finanalyzer.example.com",
  "protocol": "REST",
  "data_handling": {
    "level": "strict",
    "training_opt_out": true,
    "max_retention": "request",
    ...
  }
}
```

### Querying Agents by Data Handling Requirements

```
GET /agents?min_data_handling_level=sensitive&jurisdiction=EU&third_party_sharing=false
```

Returns only agents that meet or exceed the requested confidentiality requirements.

---

## 9. Default Behavior

- If an agent does not declare a `data_handling` policy, it defaults to `level: "open"` — **assume the worst case if not declared.**
- This applies everywhere ADHP is checked: in registries, gateways, and delegation chains. An agent in a chain that does not implement ADHP is treated as having no data policy.
- This incentivizes agents to explicitly declare their policy, as undeclared agents will be filtered out of any confidentiality-sensitive queries.

---

## 10. Relationship to Other Standards

| Standard | Focus | ADHP Complement |
|----------|-------|-----------------|
| GDPR | Legal framework for personal data in the EU | Technical declaration of compliance-relevant practices |
| HIPAA | Health data protection (US) | Agents declare health PII handling; orchestrators filter by HIPAA compliance |
| EU AI Act | AI system regulation (EU) | Machine-readable transparency for Article 50 obligations |
| ISO 27001 | Who can access data within an organization | What happens to data after an agent processes it |
| SOC 2 | Organizational security controls | Agent-level data handling transparency |
| MCP | Protocol for agent-tool communication | ADHP adds data handling metadata to the capability handshake |
| A2A | Protocol for agent-to-agent communication | ADHP enriches Agent Cards with trust information |
| MCP Gateways | Policy enforcement, auth, routing | ADHP gives gateways a standardized language for data handling enforcement |
| OAuth/OIDC | Who is authorized to call the agent | Authorization is separate — ADHP covers data handling *after* auth succeeds |

ADHP is designed to complement, not replace, these standards. An agent operating at "strict" level within the EU would still need to comply with GDPR independently — ADHP simply makes the agent's practices transparent and machine-queryable.

---

## 11. Enforcement Architecture

ADHP is declarative — it defines what agents promise. Enforcement is a separate concern that operates at multiple points in the stack:

- **Protocol level:** ADHP fields are declared in MCP `initialize` responses and A2A Agent Cards. Clients can check declarations before sending any data.
- **Gateway level:** MCP gateways read ADHP fields and enforce policies — blocking non-compliant connections, validating delegation chains, and logging audit trails. Policies can be human-defined (compliance teams) or agent-generated (dynamic based on data sensitivity).
- **Registry level:** Registries filter agents at discovery time by ADHP metadata. The [agent-registry](https://github.com/StevenJohnson998/agent-registry) project plans KYC verification and trust ratings to reduce the risk of bad-faith actors.
- **Runtime level:** Execution environments (containers, TEEs) physically constrain what agents can do with data, backing up declarations with infrastructure guarantees.

These layers are complementary. Each raises the cost of non-compliance. Combined, they make violations expensive, detectable, and attributable.

For implementation patterns at each layer and an honest assessment of their limits, see the [enforcement patterns discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/5). For how ADHP integrates as a cross-cutting concern across the stack, see the [architecture discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions/6).

---

## Contributing

This specification is in draft. We welcome feedback on:
- Are the five levels sufficient? Too many? Too few?
- Are there data handling concerns we've missed?
- How should verification work in practice?
- How does this interact with emerging AI regulation?

Please open a [Discussion](../../discussions) or submit an RFC in the `docs/` folder.
