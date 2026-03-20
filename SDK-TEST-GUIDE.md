# ADHP SDK — Test Guide

## Quick Start

```bash
# 1. SSH into the VPS
ssh deploy@46.225.18.13

# 2. Activate the virtualenv
source ~/venvs/adhp-sdk/bin/activate

# 3. Go to the repo
cd ~/agent-data-handling-policy

# 4. Start all 4 test servers
bash run-test-servers.sh

# 5. Open the test GUI
python test-gui.py &
# → Open http://46.225.18.13:9199 in your browser
```

## Test Servers

| Port | Config | Level | Compliance | Jurisdictions |
|------|--------|-------|------------|---------------|
| 9100 | healthcare.json | strict | GDPR, HIPAA | DE |
| 9101 | finance.json | strict | GDPR, AI_ACT_EU | DE, FR |
| 9102 | open_agent.json | open | (none) | (none) |
| 9103 | eu_standard.json | standard | GDPR | DE, FR, NL |

## Unit Tests

```bash
source ~/venvs/adhp-sdk/bin/activate
cd ~/agent-data-handling-policy

# Run all 60 tests
pytest -v

# Run just checker tests (24 tests)
pytest tests/test_checker.py -v

# Run just policy/config tests (25 tests)
pytest tests/test_policy.py -v

# Run integration tests (11 tests — starts its own servers)
pytest tests/test_integration.py -v
```

**Expected output:** `60 passed` with zero failures.

---

## CLI Test Scenarios

Make sure test servers are running first (`bash run-test-servers.sh`).

### Scenario 1: Compliant healthcare server
```bash
adhp check http://localhost:9100/mcp --min-level strict -c GDPR -c HIPAA
```
**Expected:** PASS — all checks green.

### Scenario 2: Open server fails strict requirements
```bash
adhp check http://localhost:9102/mcp --min-level strict
```
**Expected:** FAIL — level too low (server is 'open', required 'strict').

### Scenario 3: Jurisdiction mismatch
```bash
adhp check http://localhost:9101/mcp -j US
```
**Expected:** FAIL — server declares DE,FR; client requires US.

### Scenario 4: Finance server meets GDPR+EU requirements
```bash
adhp check http://localhost:9101/mcp --min-level strict -c GDPR -j DE -j FR
```
**Expected:** PASS.

### Scenario 5: Training opt-out on open server
```bash
adhp check http://localhost:9102/mcp --require-training-opt-out
```
**Expected:** FAIL — open server doesn't declare training opt-out.

### Scenario 6: Training opt-out on healthcare server
```bash
adhp check http://localhost:9100/mcp --require-training-opt-out
```
**Expected:** PASS — healthcare server declares training_opt_out: true.

### Scenario 7: No third-party on healthcare server
```bash
adhp check http://localhost:9100/mcp --require-no-third-party
```
**Expected:** PASS — healthcare server has third_party_opt_out: true.

### Scenario 8: No third-party on open server
```bash
adhp check http://localhost:9102/mcp --require-no-third-party
```
**Expected:** FAIL.

### Scenario 9: Retention check passes
```bash
adhp check http://localhost:9100/mcp --max-retention 24h
```
**Expected:** PASS — server retention is "request" which is less than "24h".

### Scenario 10: Retention check fails
```bash
adhp check http://localhost:9102/mcp --max-retention 24h
```
**Expected:** FAIL — open server has "unlimited" retention.

### Scenario 11: EU standard server meets basic GDPR
```bash
adhp check http://localhost:9103/mcp --min-level standard -c GDPR -j DE -j FR -j NL
```
**Expected:** PASS.

### Scenario 12: EU standard fails strict requirements
```bash
adhp check http://localhost:9103/mcp --min-level strict
```
**Expected:** FAIL — server is "standard", required "strict".

### Scenario 13: Local config check (no server needed)
```bash
adhp check-local examples/configs/healthcare.json --min-level strict -c GDPR -c HIPAA -j DE
```
**Expected:** PASS.

### Scenario 14: Validate valid config
```bash
adhp validate examples/configs/healthcare.json
```
**Expected:** "Valid ADHP config".

### Scenario 15: Validate invalid config
```bash
echo '{"level": "invalid"}' > /tmp/bad-adhp.json
adhp validate /tmp/bad-adhp.json
```
**Expected:** Validation errors shown.

### Scenario 16: Generate starter config
```bash
adhp init --level strict -c GDPR -c HIPAA -j DE --training-opt-out --third-party-opt-out
```
**Expected:** Valid JSON printed to stdout with all fields populated.

### Scenario 17: Inspect server
```bash
adhp inspect http://localhost:9100/mcp
```
**Expected:** Pretty-printed JSON of the healthcare server's ADHP declaration.

---

## GUI Test Scenarios

Open http://46.225.18.13:9199 in your browser.

### Test 1: Healthcare + GDPR
1. Select "Healthcare Server :9100"
2. Click "Fetch Policy" — should show the server's ADHP declaration
3. Set min level to "strict"
4. Type `GDPR` in compliance
5. Click "Check Compliance"
6. **Expected:** Green PASS with all checks passing

### Test 2: Open server + strict
1. Select "Open Agent :9102"
2. Set min level to "strict"
3. Click "Check Compliance"
4. **Expected:** Red FAIL — level check fails

### Test 3: Finance + US jurisdiction
1. Select "Finance Server :9101"
2. Leave level at "standard"
3. Type `US` in jurisdictions
4. Click "Check Compliance"
5. **Expected:** Red FAIL — jurisdiction check fails (server has DE,FR)

### Test 4: EU standard + GDPR + EU jurisdictions
1. Select "EU Standard :9103"
2. Set min level to "standard"
3. Type `GDPR` in compliance
4. Type `DE,FR,NL` in jurisdictions
5. Click "Check Compliance"
6. **Expected:** Green PASS

### Test 5: Multiple failures
1. Select "Open Agent :9102"
2. Set min level to "strict"
3. Type `GDPR,HIPAA` in compliance
4. Type `DE` in jurisdictions
5. Check "Require training opt-out"
6. Check "Require no third-party sharing"
7. Click "Check Compliance"
8. **Expected:** Red FAIL with multiple failing checks listed

---

## Python API Examples

```python
source ~/venvs/adhp-sdk/bin/activate
python3
```

```python
# Direct compliance check (no server needed)
from adhp import check_compliance, ADHPPolicy, ADHPClientRequirements

policy = ADHPPolicy(level="strict", training_opt_out=True, third_party_opt_out=True,
                    content_logging_opt_out=True, compliance=["GDPR"],
                    processing_jurisdiction=["DE"], storage_jurisdiction=["DE"],
                    log_jurisdiction=["DE"], max_retention="request")

req = ADHPClientRequirements(min_level="standard", require_compliance=["GDPR"],
                             accepted_jurisdictions=["DE"])

result = check_compliance(req, policy)
print(result.compliant)  # True
for c in result.checks:
    print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.reason}")
```

```python
# Gateway example
python3 examples/gateway_example.py
```

---

## Stopping Everything

```bash
# Stop test servers
bash stop-test-servers.sh

# Stop test GUI (if running in background)
kill $(lsof -ti:9199) 2>/dev/null

# Deactivate virtualenv
deactivate
```

## Rollback

If anything goes wrong:
```bash
bash ~/rollback-sdk.sh
```
This restores the repo to its pre-SDK state on the `main` branch.
