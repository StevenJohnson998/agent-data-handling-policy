# Agent Data Handling Policy (ADHP) Specification

> **Version:** 0.3.0 (Draft)
> **Status:** RFC — Request for Comments
> **Author:** Steven Johnson / ADHP Project
> **Date:** April 2026
> **License:** Apache 2.0
> **Repository:** [github.com/StevenJohnson998/agent-data-handling-policy](https://github.com/StevenJohnson998/agent-data-handling-policy)

---

## 1. Introduction

When an AI agent processes your data, what happens to it? Is it stored? Used for training? Forwarded to another service? Processed in a different country? Today there is no standard way to declare this information, and no standard way to filter based on these criteria.

ADHP is a **common language for data handling declarations**. It enables data handlers to declare their practices and data senders to declare their requirements, in a machine-readable format that supports automated matching before any data is exchanged. While designed for AI agents, the language applies to any software that processes or sends data.

### The Creative Commons Analogy

ADHP follows the Creative Commons design pattern:

- **CC did not invent copyright law** — it made it expressible in a small set of licenses. ADHP does not invent data protection law — it makes it expressible in a small set of presets.
- **CC does not crawl the web** to check license violations. ADHP does not monitor data handlers.
- **CC provides a shared vocabulary** so creators and consumers can find each other. ADHP provides a shared vocabulary so data handlers and data senders can match.

Like CC, ADHP has three layers: a machine-readable format (JSON), a human-readable summary, and a legal mapping to regulatory articles.

### What ADHP Is Not

- **Not an enforcement mechanism.** ADHP declares what data handlers commit to. How those commitments are verified or enforced is a separate concern.
- **Not a compliance certification.** Declaring `framework: "gdpr"` means the data handler's practices are designed to support GDPR obligations. It does not mean it is "GDPR certified."
- **Not a legal basis determination.** ADHP does not establish or verify lawful basis for processing (GDPR Art. 6, CCPA §1798.100). That determination remains the controller's obligation. ADHP enables systems to communicate about *how* data is handled, not *why* processing is lawful.
- **Not a substitute for processor agreements.** ADHP complements but does not replace Data Processing Agreements (Art. 28 GDPR), consent mechanisms, or Records of Processing Activities. It is the machine-readable layer that enables automated assessment — the contractual layer remains separate.
- **Not a purpose declaration.** ADHP v0.3 expresses constraints on data handling (what is NOT done) rather than processing purposes (what data is used FOR). Purpose limitation (Art. 5(1)(b) GDPR) is a planned addition for a future version.

---

## 2. Design Principles

### 2.1 Language, Not Enforcement

ADHP is a declaration language. Data handlers declare practices; data senders declare requirements; the matching algorithm determines compatibility. Enforcement — through gateways, audits, contracts, or cryptographic mechanisms — is orthogonal. A false ADHP declaration is a misrepresentation (like a false CC license claim), addressable through existing legal and contractual frameworks — or through ADHP-based solutions that may emerge to provide machine-verifiable guarantees or enforcement.

### 2.2 Familiar Foundations

ADHP addresses a problem no existing standard covers — machine-readable data handling between AI agents. Its design draws on established standards so that users encounter familiar patterns:

| Inspiration | Standard | What ADHP Borrows |
|-------------|----------|-------------------|
| Vocabulary | W3C DPV v2 | Data protection concepts (purposes, measures, categories) referenced internally in preset definitions. |
| Policy model | W3C ODRL 2.2 | The Offer/Agreement pattern, simplified to plain JSON. |
| Design pattern | Creative Commons | Three-layer design (machine/human/legal), named presets, simplicity-first. |

These standards inform ADHP's internal design but are not exposed in the developer API. ADHP's original contributions: packaging for agents, bidirectional matching, fail-closed defaults, presets, and multi-framework compliance.

### 2.3 Bidirectional by Nature

ADHP is bidirectional by definition, not as a feature. Two complementary profiles exist:

- **Policy** (data handler): "Here is what I do with data."
- **Requirements** (data sender): "Here is what I require."

Same schema structure, different semantic roles. This gives implementations freedom in how they use the profiles: for negotiation, filtering, auditing, or other purposes. Bidirectionality is inherent to the language, not prescribed by a specific workflow.

### 2.4 Fail-Closed Defaults

ADHP is designed for fail-closed interpretation. The matching algorithm (§10) treats missing or malformed declarations as the most restrictive case:

- No policy declared → data handler is treated as having no protections.
- Missing framework → no match (required frameworks not covered by any policy).
- Missing extras → no additional protections beyond the preset.
- Missing jurisdiction → no match for any jurisdiction requirement.

This incentivizes explicit declaration. How the data sender acts on a "no match" result (block, warn, log, allow with reduced trust) is up to their implementation.

### 2.5 Presets Over Properties

v0.2 had 27 fields. v0.3 has 2 always-required fields per policy (`framework`, `preset`) plus up to 5 optional fields for fine-tuning (`max_retention` is conditionally required for the `standard` preset). Named presets (`open`, `standard`, `strict`, `zero_trace`) collapse the most common configurations into a single choice. The `extras` mechanism handles edge cases without inflating the core schema.

### 2.6 Verification Is Orthogonal

ADHP profiles are self-declarations. Like CC license badges, declarations have value without verification: they make practices explicit, comparable, and filterable. By keeping verification out of the core spec, ADHP can serve as a foundation for diverse verification and enforcement methods (registries, auditor agents, cryptographic proofs, contractual frameworks) without creating a dependency on any single approach.

Future spec versions will add optional metadata fields to record that external verification occurred (e.g., auditor identity, attestation signatures, test results). ADHP is designed as a foundation layer that enables verification and enforcement systems to be built on top — it provides the standard vocabulary and structure they need to operate.

---

## 3. Terminology

ADHP uses neutral terms (`data handler`, `data sender`) rather than legal role terms (`controller`, `processor`, `sub-processor`). This is deliberate: the same software can be a controller in one deployment and a processor in another. ADHP describes the data flow direction, not the legal responsibility allocation — that mapping is external and context-dependent.

| Term | Definition |
|------|-----------|
| **Data handler** | Software that receives and processes data. In the agentic context, typically an AI agent, but can be any software. |
| **Data sender** | Software or system that sends data to a data handler. Can be a platform, an orchestrator, or another agent delegating work. |
| **Policy** | A data handler's declaration of data handling practices (what it commits to). |
| **Requirements** | A data sender's declaration of data handling expectations (what it demands). |
| **Framework** | A regulatory jurisdiction or compliance regime (e.g., GDPR, CCPA). |
| **Preset** | A named baseline of data handling guarantees within a framework. |
| **Extra** | An additional constraint that strengthens a preset. |
| **Matching** | The deterministic compatibility check between a policy and requirements. |
| **Delegation** | When a data handler forwards data to another data handler for processing. |

---

## 4. Schema

### 4.1 Policy (Data Handler)

A data handler declares its data handling practices as an array of policies. Each policy entry declares which regulatory frameworks it covers.

```json
{
  "adhp": "0.3",
  "policies": [
    {
      "id": "eu-strict",
      "frameworks": ["gdpr", "ai_act"],
      "preset": "strict",
      "extras": ["tee_execution"],
      "jurisdiction": {
        "processing": ["FR"],
        "storage": ["FR"],
        "logging": ["FR"]
      }
    },
    {
      "id": "us-standard",
      "frameworks": ["ccpa"],
      "preset": "standard",
      "extras": ["no_training"],
      "max_retention": "P1Y",
      "jurisdiction": {
        "processing": ["US"],
        "storage": ["US"]
      }
    }
  ]
}
```

A single policy entry MAY cover multiple frameworks simultaneously (e.g., `["gdpr", "ai_act"]` when the same configuration satisfies both). A data handler MAY also declare multiple policies for the same framework, offering different configurations (e.g., `gdpr:standard` with EU-wide storage and `gdpr:strict` with DE-only storage). The matching algorithm finds any compatible entry per required framework.

**Fields (top level):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `adhp` | string | Yes | Spec version this document conforms to (e.g., `"0.3"`). |
| `policies` | array | Yes | Per-framework policy declarations. At least one entry. |

**Fields (per policy):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | No | Unique identifier for this policy entry. Used in match results and policy selection. |
| `frameworks` | array of strings | Yes | Regulatory frameworks this policy covers ([§5](#5-frameworks)). At least one. |
| `preset` | string | Yes | Protection level ([§6](#6-presets)). |
| `extras` | array of strings | No | Additional constraints ([§7](#7-extras)). Defaults to `[]`. |
| `max_retention` | string | Conditional | Maximum retention duration. **Required for `standard` preset** and must be a concrete value (`none`, `session`, or ISO 8601 duration) — `legal_max` is not allowed for `standard` (use `open` if no retention commitment is made). Optional for others (defaults: `open` → `legal_max`, `strict` → `session`, `zero_trace` → `none`). Accepts either a named value (`none`, `session`, `legal_max`) or an ISO 8601 duration (P = Period prefix, T = time separator: `P7D` = 7 days, `P6M` = 6 months, `P2Y` = 2 years, `PT4H` = 4 hours). Ordering: `none` < `session` < ISO 8601 durations (ascending) < `legal_max`. |
| `jurisdiction` | object | No | Where data is processed/stored ([§9](#9-jurisdiction)). |
| `accepted_data` | array of strings | No | Data categories the data handler accepts ([§8](#8-data-categories)). Defaults to `["general"]`. |

### 4.2 Requirements (Data Sender)

Symmetrically to the policy, a data sender declares its data handling expectations as an array of requirements. Each requirement declares which frameworks it demands.

```json
{
  "adhp": "0.3",
  "require": [
    {
      "frameworks": ["gdpr"],
      "min_preset": "standard",
      "extras": ["no_log"],
      "accepted_jurisdictions": ["EU"]
    }
  ]
}
```

**Fields (per requirement):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `frameworks` | array of strings | Yes | Required regulatory frameworks. The data handler must cover all listed frameworks in a single policy entry. |
| `min_preset` | string | Yes | Minimum acceptable preset level. |
| `extras` | array of strings | No | Required extras the data handler must declare ([§7](#7-extras)). Defaults to `[]`. |
| `accepted_jurisdictions` | array of strings | No | Accepted country/region codes. See [§9.2](#92-data-sender-requirements). |
| `accepted_jurisdictions_detail` | object | No | Per-operation jurisdiction restrictions. See [§9.4](#94-per-operation-requirements). Mutually exclusive with `accepted_jurisdictions`. |
| `max_retention` | string | No | Maximum acceptable retention duration. The data handler's effective retention must not exceed this value. Same format as policy `max_retention`: named values (`none`, `session`, `legal_max`) or ISO 8601 duration. See [§10.1](#101-six-checks), check 6. |
| `data_categories` | array of strings | No | Data types the data sender will send ([§8](#8-data-categories)). |
| `policy_id` | string | No | Select a specific policy by `id` from the data handler's offerings. |

### 4.3 Minimal Valid Documents

The simplest valid policy (using `open` — no `max_retention` required):

```json
{ "adhp": "0.3", "policies": [{ "frameworks": ["gdpr"], "preset": "open" }] }
```

A minimal `standard` policy (`max_retention` is required):

```json
{ "adhp": "0.3", "policies": [{ "frameworks": ["gdpr"], "preset": "standard", "max_retention": "P1Y" }] }
```

The simplest valid requirement:

```json
{ "adhp": "0.3", "require": [{ "frameworks": ["gdpr"], "min_preset": "standard" }] }
```

---

## 5. Frameworks

Frameworks represent regulatory jurisdictions or compliance regimes. The enum is closed and extensible via spec revisions.

| ID | Regulation | Jurisdiction |
|----|-----------|--------------|
| `gdpr` | EU General Data Protection Regulation | EU/EEA |
| `uk_gdpr` | UK General Data Protection Regulation | United Kingdom |
| `ccpa` | California Consumer Privacy Act | California, US |
| `ai_act` | EU Artificial Intelligence Act | EU |
| `lgpd` | Lei Geral de Proteção de Dados | Brazil |
| `popia` | Protection of Personal Information Act | South Africa |
| `pipeda` | Personal Information Protection and Electronic Documents Act | Canada |
| `hipaa` | Health Insurance Portability and Accountability Act | US |

Adding a new framework requires defining its preset semantics and jurisdiction matrix. It does not change the schema.

> **Note:** Some frameworks listed above (`ai_act`, `hipaa`, `popia`, `pipeda`) have framework IDs defined but their per-framework preset semantics (jurisdiction matrix) are not yet published. Declaring these frameworks is valid but the legal mapping layer is pending. `gdpr`, `uk_gdpr`, and `ccpa` have the most developed preset definitions.

Both sides can declare multiple frameworks simultaneously. A data handler operating in both the EU and UK could declare a single policy covering `["gdpr", "uk_gdpr"]` when the configuration is identical, or separate policies when preset levels differ. A data sender processing EU personal data with AI could require `["gdpr", "ai_act"]` in a single requirement entry: the data handler must have a policy that covers both frameworks to match.

---

## 6. Presets

### 6.1 Ordering

Presets are strictly ordered from least to most restrictive:

```
open < standard < strict < zero_trace
```

This ordering is universal across all frameworks. A `strict` policy always satisfies a `standard` requirement, regardless of framework.

### 6.2 Definitions

| Preset | Retention | Sharing | Logging | Use Restrictions | Delegation |
|--------|-----------|---------|---------|-----------------|------------|
| `open` | `legal_max` | Allowed | Full | — | Allowed ([§11](#11-delegation)) |
| `standard` | Explicit (`max_retention` required, `legal_max` not allowed) | Allowed | Full | `no_marketing`, `no_profiling` | Allowed ([§11](#11-delegation)) |
| `strict` | `session` | Prohibited | `no_content_log` | `no_marketing`, `no_profiling`, `no_research`, `no_training` | Prohibited |
| `zero_trace` | `none` | Prohibited | `no_log` | `no_marketing`, `no_profiling`, `no_research`, `no_training`, `no_third_party` | Prohibited |

Each row is self-contained: use restrictions are listed explicitly per preset, not inherited from lower levels.

**`open`** — The data handler makes no data handling restrictions beyond framework compliance. Data retained up to the legal maximum permitted by the declared framework. Sharing and delegation are allowed. No use restrictions imposed by the preset.

> **Note on `legal_max`:** This is a functional ordering marker used in the matching algorithm, not a legal claim. In practice, "legal maximum" depends on both the declared framework and the applicable legislation in the handler's jurisdiction. GDPR Art. 5(1)(e) requires retention only as long as necessary for the declared purpose — there is no universal "maximum." For matching purposes, `legal_max` means "the longest retention the handler may lawfully apply under its declared framework." It sits at the top of the retention ordering: any ISO 8601 duration is shorter than `legal_max`.

**`standard`** — Responsible baseline. The data handler must declare an explicit `max_retention` duration (ISO 8601, `session`, or `none` — `legal_max` is not permitted; use `open` if no retention commitment is made). Sharing and delegation are allowed (delegation subject to [§11](#11-delegation) matching). No marketing use, no profiling. Logging is unrestricted. The sender can add extras (e.g., `no_training`) to further restrict handling.

**`strict`** — Strong data handling guarantees. Data retained for the session only. No third-party sharing. No content logging (metadata only). No training, no research, no marketing, no profiling. Delegation is prohibited.

**`zero_trace`** — Nothing persists. Data processed in memory only. No logging beyond the applicable legal floor. No delegation. No third-party sharing. No training, no research, no marketing, no profiling. Suitable for data that must leave absolutely no trace.

> **Note on logging and legal floor:** Logging restrictions operate above the applicable legal floor. When a handler declares multiple jurisdictions, any of those jurisdictions' legal requirements may apply depending on where and how the data is actually processed. A handler declaring `no_log` commits to retaining no more than what applicable law requires in its assessment. ADHP declarations express data handling intent; they do not substitute for legal agreements (DPAs) or regulatory compliance obligations. The sender should evaluate the handler's declared jurisdictions to assess which legal obligations may apply.

**Delegation model:** For presets that allow delegation (`open`, `standard`), delegation is governed by [§11](#11-delegation): requirements travel through the chain and each downstream handler must satisfy them via `match()`. Presets that prohibit delegation (`strict`, `zero_trace`) are equivalent to declaring the `no_delegation` extra.

> **Planned (v0.4):** Distinguish between _autonomous delegation_ (ADHP-only verification, no prior relationship) and _DPA delegation_ (covered by an explicit Data Processing Agreement between parties). v0.4 will also introduce sub-processor declarations, allowing handlers to identify their downstream partners, and an optional `legal_ref` field linking to the handler's DPA/Terms — enabling sender-side agents to verify consistency between ADHP declarations and legal documents. See also: planned `case` retention value (data retained until task completion) for purpose-bound processing.

### 6.3 Per-Framework Semantics

Presets are per-framework: `gdpr:strict` implies specific GDPR obligations (e.g., Art. 17 right to erasure, Art. 28 processor requirements), while `hipaa:strict` implies HIPAA-specific obligations. The preset ordering is universal, but the underlying regulatory mapping differs.

Framework-specific preset definitions are maintained in the **jurisdiction matrix**, a separate versioned document. The jurisdiction matrix is an internal reference for lawyers and DPOs — it is not part of the developer API.

---

## 7. Extras

Extras are additional constraints that strengthen a preset. They are drawn from a closed enum and can only add restrictions, never remove them.

### 7.1 Enum

**Data handling:**

| Extra | Effect |
|-------|--------|
| `no_training` | No ML model training on the data. |
| `no_content_log` | No content logging. Operational metadata logging (timestamps, durations, sizes, error codes) may continue. |
| `no_log` | No logging beyond the applicable legal floor. The handler retains no more than what applicable law requires in its assessment. When multiple jurisdictions are declared, any of their legal requirements may apply depending on where data is processed. |
| `no_marketing` | No use of data for direct marketing or commercial prospection. |
| `no_research` | No use of data for scientific research. |
| `no_profiling` | No automated profiling or scoring. |
| `no_third_party` | No sharing of data with third parties. |

**Delegation:**

| Extra | Effect |
|-------|--------|
| `no_delegation` | Data handler will not delegate to other data handlers. |

**Technical:**

| Extra | Effect |
|-------|--------|
| `tee_execution` | Processing occurs in a Trusted Execution Environment. |
| `encryption_at_rest` | Data is encrypted at rest. |

**Rights:**

| Extra | Effect |
|-------|--------|
| `right_to_erasure` | Data handler commits to erasing the data it holds and ensuring erasure by all downstream handlers it has delegated to, directly or through the chain. The request mechanism is implementation-defined. Consistent with GDPR Art. 17(2)/28(4) and CCPA §1798.105(c)-(d). |
| `right_to_access` | Data handler commits to honoring access requests (data subject can retrieve their data). Same cascading model as `right_to_erasure`. |
| `cascading_information` | Data handler returns `(handler_id, data_ref)` pairs after processing: its own pairs plus all pairs received from downstream handlers. Enables erasure, access, and audit across delegation chains. A handler declaring `no_delegation` trivially satisfies this by returning only its own pair. |

### 7.2 Composition with Presets

Extras compose independently with presets. A handler at any preset level can declare any extras. Presets include built-in guarantees (listed across all columns of the [§6.2](#62-definitions) table); extras add further restrictions on top.

Declaring an extra that is already structurally guaranteed by the preset (e.g., `no_third_party` on a `strict` handler, or `no_training` on a `zero_trace` handler) is valid and has no effect. Implementations MUST accept redundant extras without error.

For matching purposes (Check 3 in [§10.1](#101-six-checks)), the full set of extras satisfied by a preset is derived from ALL columns of §6.2 (not just "Use Restrictions"):

| Preset | Extras satisfied (for matching) |
|--------|-------------------------------|
| `open` | _(none)_ |
| `standard` | `no_marketing`, `no_profiling` |
| `strict` | `no_marketing`, `no_profiling`, `no_research`, `no_training`, `no_content_log`, `no_third_party`, `no_delegation` |
| `zero_trace` | `no_marketing`, `no_profiling`, `no_research`, `no_training`, `no_content_log`, `no_log`, `no_third_party`, `no_delegation` |

This table is mechanically derived from §6.2: Sharing=Prohibited → `no_third_party`; Logging=`no_content_log` → `no_content_log`; Logging=`no_log` → `no_log` + `no_content_log`; Delegation=Prohibited → `no_delegation`; Use Restrictions listed directly.

### 7.3 Governance

New extras can be added in minor spec versions (0.3.1, 0.3.2). Extras may also be deprecated or redefined when necessary. The `adhp` version field enables implementations to handle changes across spec versions.

> **Planned:** Transport security guarantee extras (encryption level, forward secrecy, relay visibility) are under consideration. These would declare transport-level guarantees without prescribing a specific protocol stack. See [Issue #12](https://github.com/StevenJohnson998/agent-data-handling-policy/issues/12).

---

## 8. Data Categories

Data categories allow data handlers to restrict which types of data they are prepared to handle (`general` is always accepted; any other category not listed is rejected), and data senders to declare which types of data they may send (the data handler must support at least all categories listed by the sender). Both fields are optional.

| Category | Description |
|----------|-------------|
| `general` | Non-personal, non-sensitive data. |
| `personal` | Personal data (names, emails, identifiers). |
| `sensitive` | Special category data (racial/ethnic origin, political opinions, health, sexual orientation). |
| `financial` | Financial records, payment data, credit information. |
| `regulated` | Data subject to sector-specific regulation (e.g., HIPAA health data, legal privilege). |
| `minor:<geo>` | Data relating to minors, with geographic scope for applicable age thresholds. |

The `minor` category uses a geographic suffix:

- `minor:FR` — specific country (ISO 3166-1 alpha-2).
- `minor:EU` — region (uses jurisdiction expansion from [§9.3](#93-region-expansion)).
- `minor:local` — resolves to the jurisdictions declared by whichever party uses it. For a data handler, this means the countries in its `jurisdiction` field. For a data sender, this means the countries in its `accepted_jurisdictions` or `accepted_jurisdictions_detail`.
- `minor:all` — any jurisdiction.

**Matching:** The data sender's `data_categories` must be a subset of the data handler's `accepted_data`. A data handler declaring `accepted_data: ["general", "personal"]` will not match a data sender sending `financial` data.

**`minor:local` matching:** `minor:local` is resolved to concrete country codes before the subset check. A data sender with `accepted_jurisdictions: ["FR", "DE"]` declaring `data_categories: ["minor:local"]` is equivalent to `["minor:FR", "minor:DE"]`. A data handler with `jurisdiction.processing: ["EU"]` declaring `accepted_data: ["minor:local"]` expands to all 27 EU minor categories. The sender's resolved set must be a subset of the handler's resolved set. If a party uses `minor:local` without declaring any jurisdiction, the category cannot be resolved and the match fails.

**Defaults and implicit inclusion:** If a data handler does not declare `accepted_data`, it defaults to `["general"]`. If a data sender does not declare `data_categories`, it defaults to `["general"]`. The `general` category is always implicitly included in a handler's `accepted_data` — a handler declaring `accepted_data: ["personal", "sensitive"]` implicitly also accepts `general` data. The effective set for matching is always `P.accepted_data ∪ {"general"}`.

---

## 9. Jurisdiction

Jurisdiction declarations are **factual**: data handlers declare where data may physically be processed and stored; data senders declare where that is acceptable. ADHP jurisdiction does not address the **legal basis for transfers** (GDPR Chapter V, adequacy decisions, Standard Contractual Clauses, Binding Corporate Rules). A handler declaring `jurisdiction.transfer: ["US"]` with `framework: "gdpr"` states a fact about data location — whether that transfer is lawful under Art. 44-49 is a separate determination that ADHP does not make.

### 9.1 Data Handler Declaration

Data handlers declare jurisdiction as an object with per-operation location arrays:

```json
"jurisdiction": {
  "processing": ["FR", "DE"],
  "storage": ["FR"],
  "logging": ["FR"],
  "transfer": ["EU"]
}
```

All values are ISO 3166-1 alpha-2 country codes or region codes (see [§9.3](#93-region-expansion)). Each operation type is optional — omitting an operation means the data handler makes no declaration about where that operation occurs.

**Operations (closed enum):**

| Operation | Definition |
|-----------|-----------|
| `processing` | Where computation on the data occurs. |
| `storage` | Where data is persisted at rest. |
| `logging` | Where operational logs containing data references are stored. |
| `transfer` | Jurisdictions through which data transits during cross-border transfers (e.g., GDPR Chapter V). |

### 9.2 Data Sender Requirements

Data senders declare where data handling is acceptable. Two modes are available (mutually exclusive):

**`accepted_jurisdictions`** applies the same constraint to all operations. Every location the data handler declares (processing, storage, logging, transfer) must fall within the accepted list.

```json
"accepted_jurisdictions": ["EU"]
```

**`accepted_jurisdictions_detail`** sets different constraints per operation type. This is useful when regulations impose stricter rules on some operations than others (e.g., storage in France but processing anywhere in the EU). Operations not listed in `accepted_jurisdictions_detail` have no geographic restriction.

```json
"accepted_jurisdictions_detail": {
  "storage": ["FR"],
  "processing": ["EU"]
}
```

### 9.3 Region Expansion

Region codes expand to their constituent countries for matching:

| Region | Expands To |
|--------|-----------|
| `EU` | AT, BE, BG, HR, CY, CZ, DK, EE, FI, FR, DE, GR, HU, IE, IT, LV, LT, LU, MT, NL, PL, PT, RO, SK, SI, ES, SE |
| `EEA` | EU + IS, LI, NO |
| `UK` | GB |

The region expansion table is maintained as a versioned data file alongside the spec. New regions can be added in minor versions.

**Matching rule:** All locations declared by the data handler must fall within the set accepted by the data sender. The check is directional: the handler's locations are tested for inclusion in the sender's accepted set, not the other way around.

- Handler declares `jurisdiction.storage: ["FR"]`, sender requires `accepted_jurisdictions: ["EU"]` → **match** (FR is within EU).
- Handler declares `jurisdiction.storage: ["FR", "US"]`, sender requires `accepted_jurisdictions: ["EU"]` → **no match** (US is outside EU).
- Handler declares `jurisdiction.storage: ["EU"]`, sender requires `accepted_jurisdictions: ["FR"]` → **no match** (EU means data could be anywhere in the EU, not guaranteed to stay in FR).

### 9.4 Per-Operation Requirements

Some regulatory contexts require different jurisdiction rules for different operations. For example, France's HDS (Hébergement de Données de Santé) requires health data to be **stored** in France but allows **processing** within the EU.

```json
{
  "frameworks": ["gdpr"],
  "min_preset": "strict",
  "accepted_jurisdictions_detail": {
    "storage": ["FR"],
    "processing": ["EU"]
  }
}
```

A data handler matches if:
- `jurisdiction.storage` locations are all within `["FR"]`
- `jurisdiction.processing` locations are all within `["EU"]` (expanded)
- `jurisdiction.logging` and `jurisdiction.transfer` have no restrictions (not specified in `accepted_jurisdictions_detail`)

---

## 10. Matching Algorithm

### 10.1 Six Checks

Matching is deterministic. It answers one question: **does the data handler's policy meet or exceed the data sender's requirements?**

The global logic is directional: a policy that is *more protective* than what is required always satisfies the requirement. "More protective" means shorter retention, more extras, tighter jurisdiction, or a higher preset. The only exception is data categories, which is a capability check (the handler must *support* the data types the sender will send).

**Definitions:**

- **R** — a single requirement entry from the data sender's `require` array.
- **P** — a single policy entry from the data handler's `policies` array.

```
For each requirement R in sender.require:

  0. POLICY SELECTION
     If R.policy_id is defined:
       Find policy P where P.id == R.policy_id. Run checks 1-6 on P.
       If not found: INCOMPATIBLE (no policy with this id).
     If R.policy_id is NOT defined:
       Find ALL policies where R.frameworks ⊆ P.frameworks.
       Run checks 2-6 on each. Any pass: COMPATIBLE (best match selected).
       None pass: INCOMPATIBLE.

  1. FRAMEWORKS (subset inclusion)
     R.frameworks ⊆ P.frameworks.
     All frameworks required by the sender must be covered by the policy.

  2. PRESET (ordered, higher = more protective)
     P.preset >= R.min_preset
     Ordering: open < standard < strict < zero_trace.

  3. EXTRAS (set inclusion, more = more protective)
     R.extras ⊆ P.extras_effective.
     P.extras_effective = P.extras ∪ preset_satisfied_extras(P.preset).
     The full set of extras satisfied by each preset is defined in §7.2
     (derived from all columns of §6.2). For example, a "strict" handler
     satisfies "no_training", "no_content_log", and "no_third_party"
     without declaring them as explicit extras.

  4. JURISDICTION (geographic inclusion, tighter = more protective)
     If R defines accepted_jurisdictions or accepted_jurisdictions_detail:
       Every location declared by P (per operation) must fall within
       the regions accepted by R (with region expansion per §9.3).
     If R defines neither: check skipped.
     A handler declaring fewer/tighter locations always satisfies
     a sender accepting a broader region.

  5. DATA CATEGORIES (capability, handler must support sender's data types)
     R.data_categories (default: ["general"]) ⊆ P.effective_accepted_data.
     P.effective_accepted_data = P.accepted_data (default: ["general"]) ∪ {"general"}.
     The "general" category is always implicitly accepted (§8).
     This is the only check where "broader = better for the handler":
     a handler accepting more data categories can serve more senders.

  6. RETENTION (ordered, shorter = more protective)
     P.effective_retention <= R.effective_max_retention.
     P.effective_retention = P.max_retention if declared,
       otherwise preset default:
         open → legal_max
         standard → INVALID (max_retention is required for standard)
         strict → session
         zero_trace → none
     R.effective_max_retention = R.max_retention if declared,
       otherwise legal_max (implicitly accepts any legal retention).
     Ordering: none < session < ISO 8601 durations (ascending) < legal_max.
     ISO 8601 durations are compared by their maximum calendar interpretation
     (P1M = 31 days, P1Y = 366 days). This is fail-closed: ambiguous durations
     are treated as their longest possible value.
     Note: `session` means data is deleted when the session/interaction ends.
     It is ordered below ISO 8601 durations because it is a purpose-bounded
     commitment (data exists only as long as contextually needed), not a
     fixed time period. A session that outlasts an ISO 8601 duration is an
     implementation concern, not a matching concern.

All requirements pass: COMPATIBLE.
Any check fails: INCOMPATIBLE.
Result includes the id of the matched policy when available.
```

**Summary of comparison operators:**

| Check | Operator | Direction |
|-------|----------|-----------|
| Frameworks | `⊆` | Required frameworks must be covered by policy |
| Preset | `>=` | Higher preset satisfies lower requirement |
| Extras | `⊆` | More extras satisfies fewer required extras |
| Jurisdiction | `⊆` | Tighter locations satisfies broader acceptance |
| Data categories | `⊆` | Broader acceptance satisfies sender's categories |
| Retention | `<=` | Shorter retention satisfies longer max requirement |

### 10.2 Match Result

The matching algorithm returns a result that serves both sides:

- **Data sender perspective:** "Is this data handler acceptable?" — at least one policy matches per required framework.
- **Data handler perspective:** "Which of my policies are compatible with this sender's requirements?" — the list of matching policies enables routing to the appropriate processing flow.

A data handler declaring multiple policies (e.g., `gdpr:strict` with FR-only storage and `gdpr:standard` with EU-wide storage) can use the match result to determine which internal flow applies to a given sender. How the handler selects among multiple compatible policies is implementation-defined (most restrictive, lowest cost, closest jurisdiction, etc.).

**Implementations SHOULD provide:**

- On success: all compatible policy entries per required framework (by `id` when available), so the handler can route and the sender can audit.
- On failure: which check(s) failed, with both values (from policy and from requirement), so that either side can understand the gap and act on it.

The following is a non-normative example of a match result:

```json
{
  "compatible": true,
  "matches": [
    {
      "frameworks": ["gdpr"],
      "compatible_policies": ["eu-strict", "eu-standard"]
    }
  ]
}
```

```json
{
  "compatible": false,
  "failures": [
    {
      "frameworks": ["gdpr"],
      "check": "jurisdiction",
      "policy_value": ["US"],
      "requirement_value": ["EU"],
      "message": "Policy jurisdiction US is outside accepted region EU"
    }
  ]
}
```

### 10.3 Fail-Closed Rules

These rules define how the matching algorithm handles absent or invalid data. The principle: missing information is never assumed to be protective.

**Failure conditions** (always INCOMPATIBLE regardless of requirements):

| Condition | Interpretation |
|-----------|---------------|
| Data handler has no ADHP document | No protections can be verified. Fails all non-trivial requirements. |
| Policy document is malformed | Treated as absent. Fails all requirements. |
| Required framework not found in handler's policies | INCOMPATIBLE for that framework. |
| Data handler omits `jurisdiction` | No jurisdiction guarantee — fails any requirement that specifies `accepted_jurisdictions` or `accepted_jurisdictions_detail`. |

**Default values** (field omitted — resolved before matching, may or may not cause failure depending on requirements):

| Omitted field | Resolved to | Consequence |
|---------------|-------------|-------------|
| Policy `extras` | `[]` (empty set) | Only fails if requirement demands specific extras not satisfied by the preset (see §7.2 table). |
| Policy `max_retention` | Preset default (`legal_max` for open, `session` for strict, `none` for zero_trace). **Invalid for `standard`** — the field is required. | Only fails if requirement specifies a shorter `max_retention`. |
| Policy `accepted_data` | `["general"]` | Only fails if sender declares `data_categories` beyond `general`. |
| Requirement `accepted_jurisdictions` / `accepted_jurisdictions_detail` | Not specified | No geographic constraint — the data handler may process, store, log, and transfer data in any location. Jurisdiction check always passes. Senders handling personal or regulated data SHOULD always specify this field, as framework compliance and local law interact in jurisdiction-dependent ways that ADHP does not resolve. |
| Requirement `max_retention` | `legal_max` | Sender implicitly accepts up to the legal maximum. Check always passes since no policy can exceed `legal_max`. |
| Requirement `extras` | `[]` (empty set) | No extras required — check always passes. |
| Requirement `data_categories` | `["general"]` | Sender only sends general data — low bar for handler. |

---

## 11. Delegation

### 11.1 Principle

When a data handler delegates work to another data handler, the requirements travel through the chain. Each downstream handler can run the same matching algorithm (§10) against the received requirements — or tighten them before passing further, but never weaken them.

```
delegate(downstream_handler, requirements):
  result = downstream_handler.match(requirements)
  if result.compatible:
    proceed with delegation
  else:
    block — downstream does not satisfy requirements
```

The `requirements` object starts as the data sender's declaration and can only become **stricter** as it travels through the chain (see §11.3 — gateways). A handler receiving requirements does not need to understand their origin or history — it runs `match()` and gets a binary answer. This keeps delegation simple and mechanically verifiable at every node.

### 11.2 Two Checks

Delegation is allowed only when BOTH conditions are met:

1. **Requirements satisfied** — the downstream handler's policies pass the full matching algorithm (all 6 checks) against the received `requirements`.
2. **Preset floor maintained** — the downstream handler's matched preset is at or above the preset of the policy under which the delegating handler is operating for this data flow. A handler operating under its `standard` policy cannot delegate to an `open` handler, even if the requirements only demand `open`.

Check 1 protects the **requirements** (met at every node). Check 2 protects the **handler's own commitment** (its declared protection level does not degrade downstream).

```
Requirements: gdpr, min_preset=standard, jurisdiction=EU, extras=[no_content_log]

Handler A (gdpr:standard, FR, max_retention=P1Y, [no_content_log, tee_execution])
  → match(requirements) ✅, preset standard
  → Delegates to Handler B, passing requirements

Handler B has three policies:
  Policy 1 (gdpr:standard, DE, P6M, [no_content_log]) → Check 1 ✅ + Check 2 ✅ (standard >= standard) → ALLOWED
  Policy 2 (gdpr:standard, US, P6M, [no_content_log]) → Check 1 ❌ (US ∉ EU) → BLOCKED
  Policy 3 (gdpr:open, FR, [no_content_log])           → Check 1 ❌ (open < standard) + Check 2 ❌ (open < standard) → BLOCKED
```

### 11.3 Rules

- **Requirements can only tighten, never loosen.** A gateway or intermediate handler may add constraints (raise `min_preset`, add `extras`, restrict `accepted_jurisdictions`, shorten `max_retention`) but may never weaken existing requirements. The `requirements` object at any point in the chain is the most restrictive union of all upstream demands.
- **`strict` and `zero_trace` prohibit delegation entirely.** A handler operating under either of these presets must process data in isolation (no sub-delegation). This is a structural guarantee of these preset levels.
- **`no_delegation` extra** explicitly prohibits all delegation regardless of preset. A sender requiring `no_delegation` blocks delegation even from `open` or `standard` handlers.

### 11.4 Cascading Information

When the `cascading_information` extra is required, the requirement propagates to all downstream handlers. Each handler in the chain returns `(handler_id, data_ref)` pairs — its own plus those received from downstream handlers. The data sender receives the full delegation map, enabling erasure or access requests across the entire chain.

---

## 12. Worked Example

A recruiting application (data sender) needs to find candidates. It processes CVs (personal data) and sends them to a recruiting agent (data handler), which delegates to a background check agent, which in turn attempts to delegate to an identity verification agent.

### Data Sender Requirements

```json
{
  "adhp": "0.3",
  "require": [
    {
      "frameworks": ["gdpr"],
      "min_preset": "standard",
      "extras": ["no_training", "cascading_information"],
      "accepted_jurisdictions": ["EU"],
      "max_retention": "P1Y",
      "data_categories": ["personal"]
    }
  ]
}
```

### Recruiting Agent (matches ✅)

```json
{
  "adhp": "0.3",
  "policies": [
    {
      "id": "recruiting-eu",
      "frameworks": ["gdpr"],
      "preset": "standard",
      "extras": ["no_training", "no_content_log", "cascading_information", "right_to_erasure"],
      "max_retention": "P6M",
      "jurisdiction": { "processing": ["DE"], "storage": ["DE"] },
      "accepted_data": ["general", "personal"]
    }
  ]
}
```

All 6 checks pass:

| Check | Requirement | Policy | Result |
|-------|-------------|--------|--------|
| 1. Frameworks | [gdpr] | [gdpr] | ✅ subset |
| 2. Preset | standard | standard | ✅ standard >= standard |
| 3. Extras | [no_training, cascading_information] | [no_training, no_content_log, cascading_information, right_to_erasure] + preset: [no_marketing, no_profiling] | ✅ subset |
| 4. Jurisdiction | EU | DE | ✅ DE ∈ EU |
| 5. Data categories | [personal] | [general, personal] | ✅ subset |
| 6. Retention | P1Y | P6M | ✅ P6M <= P1Y |

### Background Check Agent (delegation ✅)

The recruiting agent (`standard`) is allowed to delegate (§6.2). It passes the requirements to the background check agent.

```json
{
  "adhp": "0.3",
  "policies": [
    {
      "id": "bgcheck-eu",
      "frameworks": ["gdpr"],
      "preset": "standard",
      "extras": ["no_training", "cascading_information"],
      "max_retention": "P90D",
      "jurisdiction": { "processing": ["FR"], "storage": ["FR"] },
      "accepted_data": ["general", "personal"]
    }
  ]
}
```

Two checks (§11.2):

1. **Requirements satisfied:** all 6 checks pass (standard >= standard ✅, extras [no_training, cascading_information] ⊆ effective ✅, FR ∈ EU ✅, P90D <= P1Y ✅, personal ⊆ accepted ✅)
2. **Preset floor:** standard >= standard (recruiting agent's preset) ✅

Delegation allowed.

### Identity Verification Agent (delegation ❌)

```json
{
  "adhp": "0.3",
  "policies": [
    {
      "id": "idverif-global",
      "frameworks": ["gdpr"],
      "preset": "open",
      "extras": [],
      "jurisdiction": { "processing": ["US"], "storage": ["US"] },
      "accepted_data": ["general", "personal", "sensitive"]
    }
  ]
}
```

The background check agent (`standard`) attempts to delegate. Multiple checks fail:

1. **Requirements:** preset ❌ (open < standard), extras ❌ (missing `no_training`, `cascading_information`), jurisdiction ❌ (US ∉ EU)
2. **Preset floor:** open < standard (background check agent's preset) ❌

Delegation blocked — no data is sent.

```json
{
  "compatible": false,
  "failures": [
    { "frameworks": ["gdpr"], "check": "preset", "policy_value": "open", "requirement_value": "standard" },
    { "frameworks": ["gdpr"], "check": "extras", "policy_value": [], "requirement_value": ["no_training", "cascading_information"] },
    { "frameworks": ["gdpr"], "check": "jurisdiction", "policy_value": ["US"], "requirement_value": ["EU"] },
    { "frameworks": ["gdpr"], "check": "preset_floor", "policy_value": "open", "delegating_preset": "standard" }
  ]
}
```

---

## 13. Three-Layer Design

Every ADHP profile is consumable at three levels:

| Layer | Audience | Format | Purpose |
|-------|----------|--------|---------|
| **Machine** | Software, SDKs, gateways | JSON | Automated matching and filtering. |
| **Human** | Product managers, DPOs | Visual badge / summary | Quick assessment without reading JSON. |
| **Legal** | Lawyers, regulators | Article mapping | Maps each preset to specific regulatory obligations. |

The machine layer is the core specification (this document). The human and legal layers are derived artifacts that enhance adoption. A valid ADHP implementation requires only the machine layer.

---

## 14. Protocol Integration

### 14.0 Exchange Patterns

ADHP is agnostic about which side performs the matching. Two patterns are possible:

**Sender-side evaluation (recommended):** The data handler publishes or sends its policies. The data sender evaluates locally against its own requirements, which are never transmitted. The handler cannot know what the sender requires and therefore cannot fabricate a matching policy.

**Handler-side evaluation:** The data sender sends its requirements to the data handler, which evaluates against its own policies and returns compatible flows. This reveals the sender's constraints but enables handler-side routing when the handler has multiple policies.

Implementations may combine both: the handler publishes policies (sender filters), then the sender optionally sends requirements for handler-side flow selection among pre-vetted options.

**Security consideration:** If the sender reveals its requirements before seeing the handler's policies, a malicious handler could dynamically fabricate policies to appear compliant. Sender-side evaluation (or pre-published policies) mitigates this risk.

### 14.1 MCP (Model Context Protocol)

ADHP integrates with MCP via the `capabilities` object during the `initialize` handshake. The server (data handler) declares its policies; the client (data sender) evaluates locally:

```json
{
  "capabilities": {
    "adhp": {
      "adhp": "0.3",
      "policies": [
        {
          "frameworks": ["gdpr"],
          "preset": "standard",
          "extras": ["no_training"],
          "max_retention": "P2Y",
          "jurisdiction": { "processing": ["EU"], "storage": ["EU"] }
        }
      ]
    }
  }
}
```

The client reads the ADHP policy before sending any data. If no policy satisfies the client's requirements, the connection is not established. The client's requirements remain local — they are not sent to the server.

### 14.2 A2A (Agent-to-Agent Protocol)

ADHP enriches A2A Agent Cards via an extension field. Agent Cards are published in registries, enabling trust-based discovery before any connection is made:

```json
{
  "name": "FinanceAnalyzer",
  "skills": ["..."],
  "extensions": {
    "adhp": {
      "adhp": "0.3",
      "policies": [
        {
          "id": "finance-eu",
          "frameworks": ["gdpr"],
          "preset": "strict",
          "extras": ["no_log", "tee_execution"],
          "jurisdiction": { "processing": ["DE"], "storage": ["DE"] }
        }
      ]
    }
  }
}
```

Calling agents filter Agent Cards by ADHP metadata before initiating communication. Registries can pre-filter results based on a caller's requirements, returning only compatible handlers. When the caller connects, it may optionally pass its requirements for handler-side flow selection (§10.2).

---

## 15. Relationship to Existing Standards

ADHP does not replace existing standards or regulations — it provides a common vocabulary and grammar for systems to communicate about them.

### Standards Referenced

| Standard | Role in ADHP |
|----------|-------------|
| **W3C DPV v2** | Vocabulary. ADHP preset definitions reference DPV concepts internally (purposes, measures, data categories). Never exposed in the developer API. |
| **W3C ODRL 2.2** | Policy model. ADHP conceptually follows the ODRL Offer/Agreement pattern (handler offers, sender requires, matching determines compatibility). Simplified to plain JSON — ADHP does not use ODRL vocabulary terms or RDF. |
| **Creative Commons** | Design pattern. Three-layer design, presets, simplicity-first approach. |
| **IEEE 7012** | Bidirectional terms. Extended from human-to-service to agent-to-agent. |

### Regulations Supported

| Regulation | How ADHP Helps |
|-----------|---------------|
| **GDPR** | Machine-readable declaration of Art. 28 processor commitments. Enables automated sub-processor assessment across delegation chains. |
| **UK GDPR** | Same structure as EU GDPR with UK-specific supervisory authority context. Separate framework enables distinct preset semantics where regulations diverge. |
| **EU AI Act** | Transparency declarations for Art. 50 obligations. |
| **CCPA** | Third-party sharing and data sale declarations, verifiable at match time. |
| **HIPAA** | Health data handling declarations with sector-specific preset semantics. |

### Complementary Protocols

| Protocol | Relationship |
|----------|-------------|
| **MCP** | ADHP adds data handling metadata to the capability handshake ([§14.1](#141-mcp-model-context-protocol)). |
| **A2A** | ADHP enriches Agent Cards with data handling information ([§14.2](#142-a2a-agent-to-agent-protocol)). |
| **OAuth/OIDC** | Authorization is separate. ADHP covers data handling *after* auth succeeds. |
| **Gateways** | ADHP gives gateways a standardized language for data handling policy enforcement. |

---

## 16. Extensibility

### Adding Frameworks

New regulatory frameworks can be added in minor spec versions. Each new framework requires:

1. A framework ID added to the enum.
2. Preset definitions (what each preset means under that framework).
3. A jurisdiction matrix entry (internal reference for legal mapping).

Adding a framework does not change the JSON schema — existing policies remain valid.

### Adding Extras

New extras can be added in minor spec versions (0.3.1, 0.3.2). Extras may also be deprecated or redefined when necessary. The `adhp` version field enables implementations to handle changes across spec versions.

### Versioning

The `adhp` field in every document declares the spec version. Major version changes (0.3 → 0.4) may break backward compatibility. Minor changes (0.3.0 → 0.3.1) are additive only.

When a data sender and data handler declare different spec versions, behavior is implementation-defined. Implementations should document how they handle version mismatches. Detailed guidelines for implementers will be published separately.

---

## 17. Migration from v0.2

v0.3 is not backward-compatible with v0.2. Key changes:

| v0.2 | v0.3 |
|------|------|
| `level` enum (5 values) | `preset` per framework (4 values) |
| 6 boolean opt-out fields | `extras[]` enum array |
| `delegation_policy` enum | `no_delegation` extra |
| `execution_environment` enum | `tee_execution` extra |
| Flat `compliance[]` array | `frameworks` array per policy object |
| `pii_categories` array | `accepted_data` with data categories |
| `third_party_sharing` object (6 sub-fields) | `no_third_party` extra (detail in optional annex) |
| `certification` field | Out of core (verification is orthogonal) |
| `sensitive` preset | Dropped. `strict` absorbs its use cases. |
| **27 fields** | **7 per-policy fields** (2 required, 1 conditional) + 2 top-level |

---

## 18. Contributing

This specification is a draft. We welcome feedback on:

- Are four presets sufficient? Are the boundaries between them clear?
- Are there data handling constraints missing from the extras enum?
- How should the human and legal layers be designed?
- How does this interact with your regulatory context?

Please open a [Discussion](https://github.com/StevenJohnson998/agent-data-handling-policy/discussions) for ideas, an [Issue](https://github.com/StevenJohnson998/agent-data-handling-policy/issues) for bugs, or submit a PR.
