#!/usr/bin/env bash
# Quick launcher script for DroneDigitalTwin GUI Control Panel
# Compatible with both Native Linux and WSL2 (WSLg / X11).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Default DISPLAY if not set (for headless X11 / Chrome Remote Desktop / WSL2)
if [ -z "$DISPLAY" ]; then
    if [ -n "$WSL_DISTRO_NAME" ] || [ -n "$WSL_INTEROP" ]; then
        export DISPLAY=":0"
    else
        export DISPLAY=":20"
    fi
fi

VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="$(which python3)"
fi

echo "=== Starting DroneDigitalTwin + PX4 SITL GUI Control Panel ==="
echo "Project Root: $PROJECT_ROOT"
echo "Python Executable: $VENV_PYTHON"
echo "X11 DISPLAY: $DISPLAY"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

exec "$VENV_PYTHON" "$PROJECT_ROOT/gui_control_panel.py" "$@"
