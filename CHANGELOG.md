# Changelog

## [0.3.0] — 2026-04-27

### Breaking — Full spec rewrite

v0.3 is not backward-compatible with v0.2. The specification, schema, and data model are redesigned from scratch.

### Specification

**Architecture:**
- Bidirectional matching: data handlers declare policies, data senders declare requirements
- Deterministic 6-check matching algorithm (framework, preset, extras, jurisdiction, data categories, retention)
- Delegation model: requirements travel through chains, can only tighten, never loosen
- Fail-closed defaults: missing information is never assumed protective
- Three-layer design: machine (JSON), human (badge), legal (article mapping)

**Presets (4, replacing 5 levels):**
- `open` — no restrictions beyond framework compliance, legal_max retention
- `standard` — responsible baseline: explicit max_retention (mandatory, legal_max forbidden), no marketing, no profiling
- `strict` — session retention, no sharing, no content logging, no training/research/marketing/profiling, delegation prohibited
- `zero_trace` — nothing persists, no logs beyond legal floor, delegation prohibited

**Extras system:**
- Closed enum of additional constraints (replaces boolean opt-out fields)
- Split `no_log` into `no_content_log` (metadata continues) and `no_log` (legal floor only)
- New extras: `no_research`, `no_profiling`, `cascading_information`, `right_to_access`, `encryption_at_rest`
- Extras compose independently with presets; preset guarantees count as satisfied extras for matching
- Logging legal floor note: multi-jurisdiction handlers subject to any declared jurisdiction's requirements

**Frameworks:**
- `frameworks` array per policy/requirement (replacing flat `compliance[]` array and singular `framework` string)
- 8 framework IDs defined: gdpr, uk_gdpr, ccpa, ai_act, lgpd, popia, pipeda, hipaa
- Multi-framework support: single policy entry can cover multiple frameworks (e.g., `["gdpr", "ai_act"]`)
- Check 1 uses subset inclusion: `requirement.frameworks ⊆ policy.frameworks`

**Jurisdiction:**
- Per-operation location declarations (processing, storage, logging, transfer)
- Region expansion (EU → 27 countries, EEA → EU + 3)
- Per-operation requirements (`accepted_jurisdictions_detail`)
- `minor:<geo>` data category with geographic age threshold resolution

**Delegation:**
- `strict` and `zero_trace` prohibit delegation entirely
- `open` and `standard` allow delegation subject to §11 matching
- Two checks: requirements satisfied + preset floor maintained
- Gateway pattern: intermediate handlers can tighten but never loosen
- `cascading_information` extra for delegation chain transparency

**Retention:**
- ISO 8601 durations (P7D, P6M, P2Y, PT4H)
- Named values: none < session < ISO 8601 (ascending) < legal_max
- Max calendar interpretation for ambiguous durations (fail-closed)

**Protocol integration:**
- MCP: policy in `capabilities` handshake, sender-side evaluation
- A2A: policy in Agent Card `extensions`, registry pre-filtering
- Sender-side evaluation recommended (security: prevents policy fabrication)

### Schema
- New JSON Schema (draft 2020-12): `schemas/adhp-v0.3.schema.json`
- Validates all spec examples
- Enforces: standard requires max_retention, legal_max forbidden for standard
- Enforces: mutual exclusivity of accepted_jurisdictions / accepted_jurisdictions_detail
- Enforces: closed enums for frameworks, presets, extras, data categories, jurisdiction codes

### Repository
- README rewritten for v0.3
- Removed v0.2 "Five Levels" model
- Added v0.4 planned notes (Autonomous vs DPA delegation, sub-processor declarations, case retention)

### Migration from v0.2
- 27 fields → 7 per-policy (2 required, 1 conditional)
- `level` enum → `preset` per framework
- Boolean opt-outs → `extras[]` enum array
- `delegation_policy` → structural (preset-level) + `no_delegation` extra
- `sensitive` preset dropped (absorbed by `strict`)
- `processing_jurisdiction` / `storage_jurisdiction` → `jurisdiction` object with per-operation arrays

---

## [0.2.2] — 2026-03-20

### Changed
- **Breaking:** `scientific_usage_opt_in` replaced by `scientific_research_opt_out` — aligns with fail-closed philosophy (undeclared = assume worst case). Client-side `allow_scientific_usage` replaced by `require_scientific_research_opt_out`.
- Zero-trace level now requires `scientific_research_opt_out: true`
- Updated playground, schema, SDK, spec, and all examples

## [0.2.1-sdk] — 2026-03-20

### Added
- **ADHP SDK** — pip-installable Python package (`adhp/`) with compliance checker, models, CLI, server, and client
- `direct_marketing_opt_out` property (GDPR Art. 21)
- Playground support for A2A (Google Agent-to-Agent protocol), not just MCP
- 69 unit + integration tests
- Example configs: healthcare, finance, EU standard, open agent
- `pyproject.toml` for pip install

### Changed
- Playground rewritten with shared compliance logic (MCP + A2A tabs)
- Legal/regulatory claims corrected for DPO review
- SPEC.md updated with third-party sharing properties and enforcement architecture

## [0.2.1] — 2026-02-10

### Added
- `demo/` — working MCP handshake with ADHP extension (server + client + tests)
- `examples/adhp-configs/` — preset configs (healthcare, finance, open-source, zero-trace)
- `docs/` — placeholder for architecture documentation
- `CHANGELOG.md`, `CONTRIBUTING.md`, `.claude`

## [0.2.0] — 2026-02-09

### Specification
- Added Privacy & Compliance properties
- Added Section 11: Enforcement Architecture
- Updated standards table (EU AI Act, HIPAA, A2A, MCP Gateways)
- Clarified delegation rule and default behavior

### Repository
- Added `IMPLEMENTATION-GUIDE.md`
- Added `examples/` with MCP handshake, A2A Agent Card, manifests
- Added `schemas/adhp-v0.2.schema.json`
- Added `tools/validate_chain.py`
- Added GitHub Actions CI

## [0.1.0] — 2026-02-08

### Specification
- Initial ADHP specification (5 levels, core properties, delegation cascading)
- Verification roadmap (4 phases)
