# Changelog

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
