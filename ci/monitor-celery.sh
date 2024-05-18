#!/bin/bash

while true; do
    OUTPUT=$(env/bin/celery -A boxes inspect active)

    if echo "$OUTPUT" | grep -q 'empty'; then
        echo "No more tasks in the queue. Stopping Celery..."
        pkill -9 -f 'celery worker'
        break
    fi

    sleep 5
done
