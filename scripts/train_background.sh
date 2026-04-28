#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs

nohup python -u -m training.train "$@" > logs/train.out 2>&1 &
echo $! > logs/train.pid

echo "Training started (PID $(cat logs/train.pid))"
echo "  stdout/stderr: logs/train.out"
echo "  pid file:      logs/train.pid"
echo "  follow logs:   tail -f logs/train.out"
echo "  stop:          kill \$(cat logs/train.pid)"
