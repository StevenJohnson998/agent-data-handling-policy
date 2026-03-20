#!/bin/bash
# Stop all ADHP test servers
# Usage: bash stop-test-servers.sh

PIDS_FILE="/tmp/adhp-test-servers.pids"

if [ ! -f "$PIDS_FILE" ]; then
    echo "No PID file found. Servers may not be running."
    echo "Trying to kill any processes on ports 9100-9103..."
    for port in 9100 9101 9102 9103; do
        pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            kill "$pid" 2>/dev/null
            echo "  Killed PID $pid on port $port"
        fi
    done
    exit 0
fi

echo "Stopping ADHP test servers..."
while read -r pid; do
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        echo "  Stopped PID $pid"
    else
        echo "  PID $pid already stopped"
    fi
done < "$PIDS_FILE"

rm -f "$PIDS_FILE"
echo "All test servers stopped."
