# ADHP SDK — Change Record

All changes made during SDK implementation on the `feature/sdk` branch.

## Files Created

| Path | Description |
|------|-------------|
| `adhp/__init__.py` | Package exports: ADHPServer, ADHPClient, ADHPPolicy, check_compliance, etc. |
| `adhp/models.py` | Pydantic v2 models: ADHPPolicy, ADHPClientRequirements, ComplianceResult, Check, ThirdPartySharing, ThirdParty |
| `adhp/checker.py` | Core compliance logic — pure functions, 7 individual checks (level, compliance, jurisdiction, training, third-party, retention, content logging) |
| `adhp/server.py` | ADHPServer class — wraps Starlette to serve MCP with ADHP capabilities |
| `adhp/client.py` | ADHPClient class — connects to MCP servers, fetches ADHP, runs compliance check |
| `adhp/cli.py` | Click-based CLI: `adhp check`, `adhp validate`, `adhp init`, `adhp inspect`, `adhp check-local` |
| `adhp/config.py` | Config loading from JSON, YAML, env vars, dicts, or model instances |
| `adhp/schema.py` | JSON Schema validation using jsonschema against `schemas/adhp-v0.2.schema.json` |
| `adhp/policy.py` | Convenience functions: `from_file()`, `from_dict()`, `from_env()` |
| `adhp/exceptions.py` | ADHPError, ADHPConfigError, ADHPComplianceError, ADHPConnectionError, ADHPValidationError |
| `adhp/py.typed` | PEP 561 marker for typed package |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Shared pytest fixtures: open/standard/strict/zero-trace policies, various requirements |
| `tests/test_checker.py` | 24 unit tests covering all 18 compliance scenarios plus extras |
| `tests/test_policy.py` | 25 unit tests for models, config loading, schema validation |
| `tests/test_integration.py` | 11 integration tests: real HTTP server/client, CLI commands |
| `examples/configs/healthcare.json` | Strict, GDPR+HIPAA, DE jurisdiction, TEE |
| `examples/configs/finance.json` | Strict, GDPR+AI_ACT_EU, DE+FR, containerized |
| `examples/configs/open_agent.json` | Open, no restrictions |
| `examples/configs/eu_standard.json` | Standard, GDPR, DE+FR+NL, containerized |
| `examples/server_minimal.py` | 10-line minimal ADHP server example |
| `examples/server_configured.py` | Full config ADHP server with all fields |
| `examples/client_check.py` | Client that checks server compliance |
| `examples/gateway_example.py` | Gateway that filters servers by ADHP |
| `pyproject.toml` | Package metadata, dependencies, CLI entry point |
| `run-test-servers.sh` | Start 4 test servers on ports 9100-9103 |
| `stop-test-servers.sh` | Stop all test servers |
| `test-gui.py` | Web test harness on port 9199 with proxy API |
| `SDK-TEST-GUIDE.md` | Step-by-step test instructions |
| `SDK-CHANGE-RECORD.md` | This file |

## Files Modified

None. All existing files (demo/, examples/adhp-configs/, schemas/, SPEC.md, etc.) are unchanged.

## Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| HTTP framework for server | Starlette (not FastAPI) | FastAPI 0.128+ has a bug where `Request` type hint in endpoint causes 422 validation errors. Starlette handles raw requests correctly. FastAPI is still a dependency for the `[server]` extra but the core server uses Starlette directly. |
| Build backend | `setuptools.build_meta` | Standard, widely supported. Initially tried `setuptools.backends._legacy:_Backend` which doesn't exist. |
| License classifier | Removed from classifiers | setuptools 75+ enforces PEP 639 — license classifiers superseded by `license` field in `[project]`. |
| JSON Schema quirk handling | Tests account for it | The v0.2 schema's `if/then` for `max_retention=custom/session` fires even when the property is absent (JSON Schema spec behavior). Tests include explicit `max_retention` values to work around this. |
| HTTP client | httpx (primary), requests (fallback) | httpx is modern async-capable; requests fallback for environments that only have requests. |
| third_party check logic | Checks both `third_party_opt_out` flag AND `third_party_sharing.enabled` | The schema supports both the simple boolean and the detailed object; the checker accepts either. |
| DPA verification | Stubbed with field + TODO | v0.4 feature per spec roadmap. Field exists in `ADHPClientRequirements` with a TODO comment. |
| Test ports | 9150-9151 for pytest, 9100-9103 for manual | Avoids conflicts between automated and manual testing. |

## Packages Installed (in ~/venvs/adhp-sdk/)

- adhp 0.2.0 (editable install)
- pydantic 2.12.5, pydantic-core 2.41.5
- click 8.3.1
- httpx 0.28.1, httpcore 1.0.9
- fastapi 0.128.8, starlette 0.52.1
- uvicorn 0.40.0
- pytest 9.0.2, pytest-asyncio 1.3.0
- jsonschema 4.26.0
- pyyaml 6.0.3
- (plus transitive deps)

## System Changes

- Created virtualenv: `~/venvs/adhp-sdk/`
- Created backup: `~/backups/adhp-pre-sdk-*.tar.gz`
- Created rollback script: `~/rollback-sdk.sh`
- No system packages installed, no ports opened permanently, no services started
