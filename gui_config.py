#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_config.py - Configuration & Dynamic Path Resolution for DroneDigitalTwin GUI.

Instructions for Team Members:
1. Default Mode (Recommended): Leave MANUAL_* variables below as "" (empty string).
   The script will automatically enable dynamic path auto-detection based on
   environment variables, system PATH, and common installation locations.
2. Manual Override Mode: If your environment uses custom installation paths,
   simply fill in the exact absolute path strings in the MANUAL_* variables below.
"""

import os
import sys
import shutil
from pathlib import Path

# =====================================================================
# 0. Manual Override Settings
# =====================================================================
# Note: Keep as "" to enable dynamic auto-detection. Fill in an absolute
# path string to force override a specific location.
#
# Examples:
#   MANUAL_UNREAL_EDITOR_PATH = "/home/user/UnrealEngine_5.7/Engine/Binaries/Linux/UnrealEditor"
#   MANUAL_PX4_AUTOPILOT_DIR  = "/home/user/PX4-Autopilot"

MANUAL_UNREAL_EDITOR_PATH = ""  # Manual path to UnrealEditor executable (default "" for auto-detect)
MANUAL_PX4_AUTOPILOT_DIR  = ""  # Manual path to PX4-Autopilot directory (default "" for auto-detect)
MANUAL_PROJECT_ROOT       = ""  # Manual path to DroneDigitalTwin root directory (default "" for auto-detect)
MANUAL_VENV_PYTHON        = ""  # Manual path to Python virtual environment (default "" for auto-detect)


# =====================================================================
# 1. Base Directory Definitions
# =====================================================================
if MANUAL_PROJECT_ROOT and MANUAL_PROJECT_ROOT.strip():
    PROJECT_ROOT = Path(MANUAL_PROJECT_ROOT.strip())
else:
    # Default: Dynamically resolve DroneDigitalTwin root from gui_config.py location
    PROJECT_ROOT = Path(__file__).resolve().parent

if MANUAL_VENV_PYTHON and MANUAL_VENV_PYTHON.strip():
    VENV_PYTHON = Path(MANUAL_VENV_PYTHON.strip())
else:
    # Default: Auto-search venv/bin/python inside repository, fallback to system Python
    VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
    if not VENV_PYTHON.exists():
        VENV_PYTHON = Path(sys.executable)

# Script and output directories
EXAMPLE_SCRIPTS_DIR = PROJECT_ROOT / "client" / "python" / "example_user_scripts"
HALCYON_DEMO_DIR = PROJECT_ROOT / "client" / "python" / "halcyon_demo"
DEFAULT_VIDEO_DIR = str(PROJECT_ROOT / "video") + os.sep

# Helper script path for sudo keyboard control
FLY_KEYBOARD_SH = PROJECT_ROOT / "fly_keyboard.sh"


# =====================================================================
# 2. Dynamic Auto-Detection Functions
# =====================================================================
def get_unreal_editor_path() -> Path:
    """
    Locate UnrealEditor executable path dynamically:
    0. Check MANUAL_UNREAL_EDITOR_PATH override
    1. Check ENV variables: UNREAL_EDITOR_PATH or UE5_PATH
    2. Check system PATH (which UnrealEditor)
    3. Search common installation directories (~/UnrealEngine_5.x, /opt/UnrealEngine)
    """
    if MANUAL_UNREAL_EDITOR_PATH and MANUAL_UNREAL_EDITOR_PATH.strip():
        return Path(MANUAL_UNREAL_EDITOR_PATH.strip())

    env_path = os.environ.get("UNREAL_EDITOR_PATH") or os.environ.get("UE5_PATH")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    which_ue = shutil.which("UnrealEditor")
    if which_ue:
        return Path(which_ue)

    home = Path.home()
    candidates = [
        home / "UnrealEngine_5.7" / "Engine" / "Binaries" / "Linux" / "UnrealEditor",
        home / "UnrealEngine_5.6" / "Engine" / "Binaries" / "Linux" / "UnrealEditor",
        home / "UnrealEngine_5.5" / "Engine" / "Binaries" / "Linux" / "UnrealEditor",
        home / "UnrealEngine" / "Engine" / "Binaries" / "Linux" / "UnrealEditor",
        Path("/opt/UnrealEngine/Engine/Binaries/Linux/UnrealEditor"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Default fallback path
    return home / "UnrealEngine_5.7" / "Engine" / "Binaries" / "Linux" / "UnrealEditor"


def get_px4_autopilot_dir() -> Path:
    """
    Locate PX4-Autopilot repository directory dynamically:
    0. Check MANUAL_PX4_AUTOPILOT_DIR override
    1. Check ENV variable: PX4_AUTOPILOT_DIR
    2. Check sibling directory (../PX4-Autopilot)
    3. Search user home (~/PX4-Autopilot) or /src/PX4-Autopilot
    """
    if MANUAL_PX4_AUTOPILOT_DIR and MANUAL_PX4_AUTOPILOT_DIR.strip():
        return Path(MANUAL_PX4_AUTOPILOT_DIR.strip())

    env_path = os.environ.get("PX4_AUTOPILOT_DIR")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    candidates = [
        PROJECT_ROOT.parent / "PX4-Autopilot",
        Path.home() / "PX4-Autopilot",
        Path("/src/PX4-Autopilot"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return PROJECT_ROOT.parent / "PX4-Autopilot"


UNREAL_EDITOR_PATH = get_unreal_editor_path()
PX4_AUTOPILOT_DIR = get_px4_autopilot_dir()


# =====================================================================
# 3. Map Projects Registry
# =====================================================================
MAP_PROJECTS_DATA = [
    ("map_river_forest", PROJECT_ROOT / "unreal" / "LowPolyRiverForest" / "ForestDomeEnv.uproject"),
    ("map_blocks", PROJECT_ROOT / "unreal" / "Blocks" / "Blocks.uproject"),
]

walking_npcs_path = PROJECT_ROOT / "unreal" / "WalkingNPCs" / "WalkingNPCs.uproject"
if walking_npcs_path.exists():
    MAP_PROJECTS_DATA.append(("map_walking_npcs", walking_npcs_path))
