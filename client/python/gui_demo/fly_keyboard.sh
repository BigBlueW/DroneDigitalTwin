#!/usr/bin/env bash
# Fly Drone1 with the keyboard via px4_astar_autopilot.py --keyboard-control.
# Must run with sudo: the Linux 'keyboard' package needs root to read global key events.
set -e
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT/client/python/example_user_scripts"
exec "$ROOT/venv/bin/python" px4_astar_autopilot.py \
  --keyboard-control \
  --px4-ready-timeout-sec 300
