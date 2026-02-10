#!/bin/bash
# ADHP Demo — Security & Functionality Test Suite
# Usage: bash test_security.sh [BASE_URL]

set -e

BASE_URL="${1:-http://localhost:8910}"
PASS=0
FAIL=0

green() { echo -e "\033[32m✅ $1\033[0m"; PASS=$((PASS+1)); }
red()   { echo -e "\033[31m❌ $1\033[0m"; FAIL=$((FAIL+1)); }
info()  { echo -e "\033[34mℹ️  $1\033[0m"; }

echo "============================================"
echo "ADHP Demo Security & Functionality Tests"
echo "Target: $BASE_URL"
echo "============================================"
echo ""

# 1. Valid initialize
info "Test 1: Valid MCP initialize request"
RESP=$(curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","clientInfo":{"name":"test","version":"1.0"}}}')
if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['result']['capabilities']['adhp']['level']" 2>/dev/null; then
  green "Initialize returns ADHP in capabilities"
else
  red "Initialize missing ADHP (response: $RESP)"
fi

# 2. ADHP fields complete
info "Test 2: ADHP fields are complete"
if echo "$RESP" | python3 -c "
import sys,json
adhp = json.load(sys.stdin)['result']['capabilities']['adhp']
required = ['level','training_opt_out','max_retention','compliance','third_party_sharing']
missing = [f for f in required if f not in adhp]
assert not missing, f'Missing: {missing}'
" 2>/dev/null; then
  green "All required ADHP fields present"
else
  red "Missing ADHP fields"
fi

# 3. MCP structure
info "Test 3: MCP response structure"
if echo "$RESP" | python3 -c "
import sys,json
d = json.load(sys.stdin)
assert d['jsonrpc'] == '2.0'
assert d['id'] == 1
assert 'protocolVersion' in d['result']
assert 'serverInfo' in d['result']
assert 'capabilities' in d['result']
" 2>/dev/null; then
  green "Valid MCP JSON-RPC 2.0 response structure"
else
  red "Invalid MCP response structure"
fi

# 4. Reject GET
info "Test 4: Reject GET on /mcp"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/mcp")
if [ "$HTTP_CODE" = "405" ]; then
  green "GET /mcp returns 405"
else
  red "GET /mcp returned $HTTP_CODE (expected 405)"
fi

# 5. Reject unknown methods
info "Test 5: Reject unknown JSON-RPC method"
RESP=$(curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
if echo "$RESP" | grep -q "Method not found"; then
  green "Unknown method rejected"
else
  red "Unknown method not rejected"
fi

# 6. Reject invalid JSON
info "Test 6: Reject invalid JSON body"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d 'not json at all')
if [ "$HTTP_CODE" = "400" ]; then
  green "Invalid JSON returns 400"
else
  red "Invalid JSON returned $HTTP_CODE (expected 400)"
fi

# 7. Reject oversized body
info "Test 7: Reject oversized request (>4KB)"
LARGE_BODY=$(python3 -c "import json; print(json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'data':'x'*5000}}))")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d "$LARGE_BODY")
if [ "$HTTP_CODE" = "413" ]; then
  green "Oversized request returns 413"
else
  red "Oversized request returned $HTTP_CODE (expected 413)"
fi

# 8. Reject missing jsonrpc
info "Test 8: Reject missing jsonrpc version"
RESP=$(curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"id":1,"method":"initialize","params":{}}')
if echo "$RESP" | grep -q "2.0"; then
  green "Missing jsonrpc field rejected"
else
  red "Missing jsonrpc field not caught"
fi

# 9. Health endpoint
info "Test 9: Health check endpoint"
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  green "Health endpoint working"
else
  red "Health endpoint failed"
fi

# 10. No docs exposed
info "Test 10: No docs endpoints exposed"
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
REDOC_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/redoc")
OPENAPI_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/openapi.json")
if [ "$DOCS_CODE" = "404" ] && [ "$REDOC_CODE" = "404" ] && [ "$OPENAPI_CODE" = "404" ]; then
  green "No docs/redoc/openapi exposed"
else
  red "Docs endpoints accessible (docs=$DOCS_CODE redoc=$REDOC_CODE openapi=$OPENAPI_CODE)"
fi

# 11. Ping
info "Test 11: MCP ping method"
RESP=$(curl -s -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":99,"method":"ping","params":{}}')
if echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['id']==99 and 'result' in d" 2>/dev/null; then
  green "Ping returns valid response"
else
  red "Ping failed"
fi

# 12. Rate limiting (LAST — burns through the quota)
info "Test 12: Rate limiting (sending 12 rapid requests)"
sleep 61  # ensure clean rate limit window
RATE_LIMITED=false
for i in $(seq 1 12); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/mcp" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
  if [ "$HTTP_CODE" = "429" ]; then
    RATE_LIMITED=true
    break
  fi
done
if [ "$RATE_LIMITED" = true ]; then
  green "Rate limiting triggered at request $i"
else
  red "Rate limiting not triggered after 12 requests"
fi

echo ""
echo "============================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================"
[ "$FAIL" -gt 0 ] && exit 1
