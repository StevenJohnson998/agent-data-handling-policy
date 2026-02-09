# Agent Data Handling Policy (ADHP) Specification

> **Version:** 0.2.0 (Draft)
> **Status:** RFC -- Request for Comments
> **Authors:** Agent Registry Project
> **Date:** February 2026
> **License:** Apache 2.0
> **Changelog:** [v0.1 to v0.2](#changelog)

---

## 1. Purpose

In a multi-agent ecosystem, when an orchestrator sends data to an agent for processing, the sender needs to know: **what will happen to my data?**

Traditional security frameworks (ISO 27001, GDPR) focus on *who can access data*. ADHP addresses a different question specific to the agentic world: **what does the agent do with the data during and after processing?**

This specification defines a standardized, machine-readable way for AI agents to declare their data handling practices, enabling orchestrators to make informed routing decisions based on the sensitivity of the data being processed.

---

## 2. Problem Statement

When Agent A sends a financial document to Agent B for analysis:

- Will Agent B use that document to train or improve its model?
- Will Agent B store the document after returning the analysis? For how long?
- Will Agent B log the contents of the document?
- Will Agent B forward the document to a sub-agent (Agent C)? With what guarantees?
- Will Agent B's response contain the original sensitive data?
- Will Agent B share the data with third parties? Which ones?
- Where physically is Agent B processing and storing the data?
- Is Agent B compliant with the regulations I care about?
- What types of personal data does Agent B protect?

Today, there is no standard way for agents to declare this information, and no standard way for orchestrators to filter agents based on these criteria.

---

## 3. Data Handling Levels

ADHP defines five levels of data handling, from most permissive to most restrictive.

### 3.1 Summary Table

| Level | Label | Training | Retention | Logging | Delegation | Output | Third-Party Sharing |
|-------|-------|----------|-----------|---------|------------|--------|---------------------|
| 0 | **open** | Allowed | Unlimited | Full content | Unrestricted | May contain source data | Allowed |
| 1 | **standard** | No | Defined period | Allowed | Caller's level minimum | May contain derived data | With consent |
| 2 | **sensitive** | No | Request or short-term | Metadata only | Caller's level+, declared | Sanitized | Anonymized only |
| 3 | **strict** | No | Request only | None | Caller's level+ only | Sanitized + reviewed | Not allowed |
| 4 | **zero-trace** | No | None (memory only) | None | No delegation | Sanitized, nothing leaves agent | Not allowed |

### 3.2 Detailed Definitions

#### Level 0 -- Open

The agent makes no guarantees about data handling. Data may be used for any purpose including model training, indefinite storage, and redistribution. This is the **default assumption** when an agent does not declare a policy.

**Use case:** Public data processing, open-source analysis, non-sensitive content generation.

#### Level 1 -- Standard

The agent will not use the data for model training. Data is retained for a defined period (declared via `max_retention` and optionally `retention_days`). Content logging is permitted but should be declared via the `content_logging` property.

An agent at Level 1 may retain data beyond a single session to support features like conversation history. The exact retention period must be declared. If `max_retention` is `session`, the `session_ttl` property defines the duration.

**Use case:** General business operations, non-regulated internal data, standard API calls, conversational agents with memory.

#### Level 2 -- Sensitive

Same protections as Standard, with additional constraints: retention is limited to single requests or short defined periods. Output is sanitized -- it will not contain verbatim source data. Specific PII categories are protected (declared via `pii_categories`). If the agent delegates, this must be declared in the manifest. Third-party sharing is only permitted with anonymized data.

**Use case:** Personal data processing, financial analysis, HR data, customer records.

#### Level 3 -- Strict

The agent provides strong confidentiality guarantees. No content logging of any kind. Data is retained only during request processing. Delegation is only permitted to agents that meet the caller's requested level or higher. Output is sanitized and reviewed (automated or manual) to prevent data leakage. No third-party sharing of any kind.

**Use case:** Legal documents, trade secrets, medical records, classified business strategies.

#### Level 4 -- Zero-Trace

The highest level of confidentiality. The agent processes data in memory only -- no disk writes at any point. No logging whatsoever. No delegation to any other agent. Output is sanitized and constrained so that no source data leaves the agent boundary. Data leaves no trace after processing.

Agents declaring Level 4 SHOULD declare their `execution_environment` to substantiate this claim (see Section 4.3).

**Use case:** National security, pre-announcement M&A data, whistleblower submissions, highly sensitive IP.

---

## 4. Data Handling Properties

Beyond the overall level, each agent declares specific properties in its manifest.

### 4.1 Core Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `level` | enum | **Yes** | `open`, `standard`, `sensitive`, `strict`, `zero-trace` |
| `training_opt_out` | boolean | **Yes** | Agent commits to NOT using data for model training |
| `max_retention` | enum | **Yes** | `none`, `request`, `session`, `24h`, `7d`, `30d`, `custom`, `unlimited` |
| `retention_days` | integer | No | Exact days when `max_retention` is `custom`. Must be >= 0. |
| `session_ttl` | string | No | When `max_retention` is `session`, the duration: `1h`, `4h`, `8h`, `24h`. Required if max_retention is `session`. |
| `content_logging` | boolean | **Yes** | Whether request/response content appears in logs |
| `delegation_policy` | enum | **Yes** | `none`, `same_or_higher`, `unrestricted` |
| `output_sanitization` | boolean | **Yes** | Whether outputs are scrubbed of source data |
| `certification` | string | No | Future: ID of a verification/audit certificate |

### 4.2 Privacy & Compliance Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `compliance` | list[string] | No | Regulatory frameworks the agent complies with |
| `pii_categories` | list[string] | No | PII types actively protected by the agent |
| `processing_jurisdiction` | list[string] | No | Where the AI model runs (ISO 3166-1 alpha-2 codes) |
| `storage_jurisdiction` | list[string] | No | Where data is stored at rest |
| `log_jurisdiction` | list[string] | No | Where logs are stored |
| `execution_environment` | enum | No | `standard`, `containerized`, `TEE`, `enclave` |

#### 4.2.1 Compliance Values

The `compliance` field accepts any string, but the following values are standardized:

| Value | Regulation |
|-------|-----------|
| `GDPR` | General Data Protection Regulation (EU) |
| `HIPAA` | Health Insurance Portability and Accountability Act (US) |
| `CCPA` | California Consumer Privacy Act (US) |
| `POPIA` | Protection of Personal Information Act (South Africa) |
| `PIPEDA` | Personal Information Protection and Electronic Documents Act (Canada) |
| `LGPD` | Lei Geral de Protecao de Dados (Brazil) |
| `AI_ACT_EU` | EU Artificial Intelligence Act |
| `SOC2` | SOC 2 Type II certified |
| `ISO27001` | ISO 27001 certified |

#### 4.2.2 PII Category Values

| Value | Data Types Covered |
|-------|-------------------|
| `email` | Email addresses |
| `phone` | Phone numbers |
| `financial` | Bank accounts, credit cards, tax IDs, salary data |
| `health` | Medical records, diagnoses, prescriptions, health metrics |
| `identity` | Full names, government IDs, passport numbers, dates of birth |
| `location` | Physical addresses, GPS coordinates, IP-based geolocation |
| `biometric` | Fingerprints, facial recognition data, voice prints |

#### 4.2.3 Execution Environment Values

| Value | Description |
|-------|-------------|
| `standard` | Standard server or cloud instance |
| `containerized` | Isolated container (Docker, etc.) with no persistent storage |
| `TEE` | Trusted Execution Environment -- hardware-isolated processing |
| `enclave` | Secure enclave (AWS Nitro, Intel SGX, AMD SEV) -- strongest hardware guarantee |

### 4.3 Third-Party Sharing Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `third_party_sharing.enabled` | boolean | **Yes** | Whether data is shared with any third party |
| `third_party_sharing.parties` | list[object] | No | Declared third parties (see below) |
| `third_party_sharing.opt_out_available` | boolean | No | Whether the data sender can opt out of sharing |

Each entry in `third_party_sharing.parties`:

| Property | Type | Description |
|----------|------|-------------|
| `name` | string | Name of the third party |
| `type` | enum | `agent` (in registry), `non_agent` (external service), `undisclosed` |
| `purpose` | enum | `analytics`, `advertising`, `improvement`, `subprocessing`, `legal`, `resale` |
| `data_shared` | list[string] | What categories of data are shared |
| `adhp_level` | string | The third party's ADHP level if known, `null` if unknown |
| `registry_id` | string | If `type` is `agent`, the registry ID for chain validation |

**Critical rule:** If a third party has `type: "undisclosed"` or `adhp_level: null`, that party is treated as **Level 0** for delegation chain validation purposes. This incentivizes full disclosure.

### 4.4 Full Manifest Example

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
    "pii_categories": ["email", "phone", "financial", "identity"],
    "processing_jurisdiction": ["DE"],
    "storage_jurisdiction": ["DE"],
    "log_jurisdiction": ["DE"],
    "execution_environment": "containerized",
    "certification": null,
    "third_party_sharing": {
      "enabled": false,
      "parties": [],
      "opt_out_available": true
    }
  }
}
```

---

## 5. Delegation Cascading Rule

### 5.1 Core Principle

When a caller requests data processing at a certain ADHP level, **every agent in the delegation chain must meet or exceed the caller's requested level.**

The constraint is defined by the **caller's requirement**, not the delegating agent's own level. A Level 4 agent handling a Level 1 request may delegate to any Level 1+ agent.

### 5.2 Cascading Table

| Caller Requests | Minimum Level for ALL Agents in Chain |
|----------------|--------------------------------------|
| open | open (any) |
| standard | standard or above |
| sensitive | sensitive or above |
| strict | strict or above |
| zero-trace | No delegation allowed (inherent to Level 4) |

### 5.3 Validation Rules

1. The caller's requested level is the **floor** for the entire chain.
2. Each agent's `delegation_policy` must permit delegation (not `none`).
3. Level 4 agents MUST NOT delegate regardless of the caller's request level.
4. Third parties with unknown ADHP levels (`null`) are treated as Level 0.
5. If any agent in the chain fails validation, the **entire chain is invalid**.

### 5.4 Example

```
Caller requests: Level 2 (sensitive)

Chain: Agent A (strict) -> Agent B (sensitive) -> Agent C (strict)
Result: VALID
Reason: All agents are Level 2 or above.

Chain: Agent A (strict) -> Agent B (standard) -> Agent C (strict)
Result: INVALID
Reason: Agent B (Level 1) is below the caller's Level 2 requirement.

Chain: Agent A (zero-trace) -> Agent B (strict)
Result: INVALID
Reason: Level 4 agents cannot delegate.
```

---

## 6. Third-Party Sharing Rules

| Agent Level | Sharing Allowed | Conditions |
|-------------|----------------|------------|
| open | Yes | No restrictions |
| standard | Yes | Only with sender's consent |
| sensitive | Limited | Only anonymized/sanitized data |
| strict | No | Third-party sharing prohibited |
| zero-trace | No | No data leaves agent boundary |

When third-party sharing is enabled, the effective ADHP level of the agent (from the caller's perspective) is the **minimum** of the agent's own level and the lowest known third-party level.

Example: An agent declares Level 2 but shares data with a `type: "undisclosed"` third party. Effective level for the caller: **Level 0**.

---

## 7. Protocol Integration

### 7.1 MCP (Model Context Protocol)

ADHP can be integrated into MCP as a server capability declared during the `initialize` handshake:

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
        "training_opt_out": true,
        "max_retention": "request",
        "compliance": ["GDPR"],
        "pii_categories": ["email", "financial", "health"],
        "processing_jurisdiction": ["DE"],
        "execution_environment": "containerized"
      }
    },
    "serverInfo": {
      "name": "FinanceAnalyzer Pro",
      "version": "1.0.0"
    }
  }
}
```

**Behavior:** An MCP client checks the `adhp` capability before sending any data. If the server's ADHP level does not meet the client's requirements, the client disconnects without sending data. This is a **client-side** enforcement mechanism -- the protocol itself does not block communication.

### 7.2 A2A (Agent-to-Agent)

ADHP extends the A2A Agent Card with a top-level `adhp` field:

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

### 7.3 REST API / Registry

For registries (including the [Agent Registry](https://github.com/StevenJohnson998/agent-registry) reference implementation), ADHP is part of the agent registration payload:

```
POST /agents
{
  "name": "FinanceAnalyzer Pro",
  "capabilities": ["financial-analysis"],
  "data_handling": { ... ADHP properties ... }
}

GET /agents?min_adhp_level=strict&compliance=GDPR&processing_jurisdiction=DE
```

---

## 8. Default Behavior

- If an agent does not declare a `data_handling` policy, assume **Level 0** (open).
- If a property is missing, assume the least restrictive interpretation.
- If `third_party_sharing` is not declared, assume sharing is enabled with undisclosed parties (effective Level 0).

This "assume the worst" default incentivizes agents to declare their policies explicitly.

---

## 9. Verification Roadmap

### Phase 1 -- Self-Declaration (Current)

Agents declare their own data handling level. Orchestrators filter based on declared levels. Trust is based on the agent operator's reputation.

### Phase 2 -- Operator Verification

Agent operators undergo identity verification (KYC). Verified operators receive a badge. Technical review of declared ADHP properties against actual infrastructure.

### Phase 3 -- Automated Auditing

Trusted auditor agents periodically test registered agents by sending test data with tracking markers, verifying data is handled according to declared policy, checking delegation chains, and reporting violations.

### Phase 4 -- Cryptographic Verification

Technical enforcement through encrypted data envelopes, cryptographic proofs of deletion, Verifiable Credentials (W3C VC) for signed ADHP manifests, and TEE attestation for Level 4 claims.

---

## 10. Relationship to Other Standards

| Standard | Focus | How ADHP Complements It |
|----------|-------|------------------------|
| GDPR | Legal framework for personal data (EU) | ADHP makes GDPR-relevant practices machine-queryable |
| HIPAA | Health data protection (US) | Agents declare health PII handling; orchestrators filter by HIPAA compliance |
| CCPA | Consumer privacy (California) | ADHP exposes opt-out and data sharing practices |
| AI Act (EU) | AI system regulation | ADHP supports transparency obligations for AI agents |
| ISO 27001 | Organizational security controls | ADHP operates at the agent level, not the organization level |
| SOC 2 | Trust service criteria | ADHP is real-time and per-request; SOC 2 is periodic audit |
| MCP | Protocol for agent-tool communication | ADHP adds data handling metadata to the capability handshake |
| A2A | Protocol for agent-to-agent communication | ADHP enriches Agent Cards with trust information |
| OAuth/OIDC | Authentication and authorization | ADHP is about data handling *after* authentication succeeds |

---

## 11. Audit Mode (Informative)

Implementations MAY support an **audit mode** where ADHP policies are evaluated but not enforced. In audit mode:

- All data flows proceed normally
- A log records what WOULD have been blocked or flagged
- No requests are rejected based on ADHP level mismatches

This is useful for onboarding (understanding data flows before enforcing policies), compliance preparation (generating evidence of what protections are needed), and testing (validating ADHP declarations against actual behavior).

---

## 12. Reference Implementation Patterns (Informative)

This section describes common patterns for achieving each ADHP level. These are suggestions, not requirements.

| Level | Pattern | Tools |
|-------|---------|-------|
| 0-1 | Standard server with configurable logging and retention | Any server framework |
| 2 | PII tokenization proxy between client and agent | Skyflow, Piiano, or open-source vault |
| 3 | Output guard validates no source data leaks before response | LlamaGuard, custom classifier |
| 4 | Memory-only processing in hardware-isolated environment | AWS Nitro Enclaves, Intel SGX, AMD SEV |

---

## Changelog

### v0.2.0 (February 2026)

**New properties:**
- `compliance` -- regulatory framework tags (GDPR, HIPAA, etc.)
- `pii_categories` -- granular PII type protection declaration
- `processing_jurisdiction`, `storage_jurisdiction`, `log_jurisdiction` -- replaces single `jurisdiction` field
- `execution_environment` -- infrastructure type (standard, TEE, enclave)
- `session_ttl` -- explicit session duration when max_retention is session
- `retention_days` -- custom retention period support
- `third_party_sharing.parties` -- detailed third-party disclosure with type and ADHP level

**Changed:**
- Delegation cascading rule now based on **caller's requested level**, not delegating agent's level
- Level 1 retention changed from "session-based" to "defined period" to accommodate conversation history
- Third parties with unknown ADHP level treated as Level 0

**New sections:**
- Protocol integration (MCP handshake, A2A Agent Card, REST API)
- Audit mode
- Reference implementation patterns
- Compliance and PII category value tables

### v0.1.0 (February 2026)

Initial draft with five levels, core properties, delegation cascading, and verification roadmap.

---

## Contributing

This specification is a draft seeking community feedback. Please open a Discussion or Issue.

Key questions we'd welcome input on:
- Are the five levels right? Too many? Too few?
- Is the delegation cascading rule practical?
- What data handling concerns are we missing?
- How should verification work?
- How does this interact with AI regulation in your jurisdiction?
- What PII categories or compliance frameworks should we add?
