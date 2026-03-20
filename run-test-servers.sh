#!/bin/bash
# Start 4 ADHP test servers with different configs on ports 9100-9103
# Usage: bash run-test-servers.sh

set -e

VENV=~/venvs/adhp-sdk
REPO_DIR=~/agent-data-handling-policy
CONFIGS_DIR="$REPO_DIR/examples/configs"
PIDS_FILE="/tmp/adhp-test-servers.pids"

if [ -f "$PIDS_FILE" ]; then
    echo "Test servers may already be running. Run stop-test-servers.sh first."
    echo "Or remove $PIDS_FILE if they are not running."
    exit 1
fi

source "$VENV/bin/activate"

echo "Starting ADHP test servers..."
echo ""

# Server 1: Healthcare (strict, GDPR+HIPAA, DE)
python3 -c "
from adhp import ADHPServer
server = ADHPServer(name='Healthcare Server', version='1.0.0', config='$CONFIGS_DIR/healthcare.json')
server.run(host='0.0.0.0', port=9100)
" &
echo "$!" >> "$PIDS_FILE"
echo "  [9100] Healthcare Server (strict, GDPR+HIPAA, DE) — PID $!"

# Server 2: Finance (strict, GDPR+AI_ACT_EU, DE+FR)
python3 -c "
from adhp import ADHPServer
server = ADHPServer(name='Finance Server', version='1.0.0', config='$CONFIGS_DIR/finance.json')
server.run(host='0.0.0.0', port=9101)
" &
echo "$!" >> "$PIDS_FILE"
echo "  [9101] Finance Server (strict, GDPR+AI_ACT_EU, DE+FR) — PID $!"

# Server 3: Open Agent (open, no restrictions)
python3 -c "
from adhp import ADHPServer
server = ADHPServer(name='Open Agent', version='1.0.0', config='$CONFIGS_DIR/open_agent.json')
server.run(host='0.0.0.0', port=9102)
" &
echo "$!" >> "$PIDS_FILE"
echo "  [9102] Open Agent (open, no restrictions) — PID $!"

# Server 4: EU Standard (standard, GDPR, DE+FR+NL)
python3 -c "
from adhp import ADHPServer
server = ADHPServer(name='EU Standard Server', version='1.0.0', config='$CONFIGS_DIR/eu_standard.json')
server.run(host='0.0.0.0', port=9103)
" &
echo "$!" >> "$PIDS_FILE"
echo "  [9103] EU Standard Server (standard, GDPR, DE+FR+NL) — PID $!"

echo ""
echo "Waiting for servers to start..."
sleep 2

# Health checks
ALL_OK=true
for port in 9100 9101 9102 9103; do
    if curl -s "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
        echo "  [OK] Port $port is healthy"
    else
        echo "  [FAIL] Port $port did not respond"
        ALL_OK=false
    fi
done

echo ""
if $ALL_OK; then
    echo "All 4 test servers running. PIDs saved to $PIDS_FILE"
    echo "Stop with: bash stop-test-servers.sh"
else
    echo "WARNING: Some servers failed to start. Check logs above."
fi
