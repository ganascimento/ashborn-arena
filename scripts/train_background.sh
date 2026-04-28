#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

if [ -f logs/train.pid ] && kill -0 "$(cat logs/train.pid)" 2>/dev/null; then
    echo "Training already running (PID $(cat logs/train.pid))" >&2
    echo "Stop it first: kill \$(cat logs/train.pid)" >&2
    exit 1
fi

rm -f logs/train.out logs/train.pid

nohup python -u -m training.train "$@" > logs/train.out 2>&1 &
echo $! > logs/train.pid

echo "Training started (PID $(cat logs/train.pid))"
echo "  stdout/stderr: logs/train.out"
echo "  pid file:      logs/train.pid"
echo "  follow logs:   tail -f logs/train.out"
echo "  stop:          kill \$(cat logs/train.pid)"
