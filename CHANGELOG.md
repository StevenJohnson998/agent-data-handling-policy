# Changelog

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
