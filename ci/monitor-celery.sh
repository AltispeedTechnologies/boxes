#!/bin/bash
# monitor-celery.sh - operational helper to watch Celery worker queue drain.
# Uses the project virtualenv celery binary. See docs/CELERY.md.
#
# Intended to run from the repository root so ./env/bin/celery resolves.
# When the worker reports no active tasks, stops celery worker processes.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CELERY_BIN="${REPO_ROOT}/env/bin/celery"

if [ ! -x "$CELERY_BIN" ]; then
    echo "error: celery not found at $CELERY_BIN" >&2
    exit 1
fi

while true; do
    OUTPUT="$("$CELERY_BIN" -A boxes inspect active)" || true

    if echo "$OUTPUT" | grep -q 'empty'; then
        echo "No more tasks in the queue. Stopping Celery..."
        pkill -9 -f 'celery worker' || true
        break
    fi

    sleep 5
done
