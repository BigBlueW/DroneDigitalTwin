# Team Project Wiki: Swarm & AI Simulation

This document serves as a development guide for the **Drone Swarm & AI** project using Project AirSim.

## 1. Environment & Setup

### Automated Setup (Recommended)
Run the one-click setup script from the repository root. It will install all prerequisites, create the Python virtual environment, and build the project:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\setup_windows.ps1
```

### Manual Setup
If you prefer to set up manually, or the script has already been run and you just need to activate the environment:

#### Create and Activate Virtual Environment
If you are setting this up for the first time:
```powershell
# 1. Create venv
python -m venv venv

# 2. Activate venv
.\venv\Scripts\activate
```

### Install Dependencies
Run these commands within the activated `venv`:
```powershell
# Core AirSim dependencies
pip install -r client/python/projectairsim/requirements.txt

# Install the projectairsim package in editable mode
pip install -e client/python/projectairsim/

# Additional tools for examples
pip install keyboard
```

### Launch Unreal Project
```powershell
# Open the Blocks project (AirSim Core)
Start-Process unreal\Blocks\Blocks.uproject
```

---

## 2. Initial Testing
Before starting complex development, ensure the toolchain is working.

1. **Unreal**: Open `Blocks.uproject` and press **Play**.
2. **Terminal**: Run these test scripts from `client/python/example_user_scripts/`:

```powershell
.\venv\Scripts\activate

cd client/python/example_user_scripts/
```

**Basic Flight Test**:
```powershell
python hello_drone.py
```

**Manual Control Test**:
```powershell
python keyboard_control.py
```

**Note**: Always stop the python script before stopping the unreal project.

---

## 3. Standard Simulation Workflow
1. **Unreal**: Open `Blocks.uproject`.
2. **Unreal**: Select your Map (e.g., `BlocksMap` or `NewMap`).
3. **Unreal**: Set `GameMode Override` to **`ProjectAirSimGameMode`** in World Settings.
4. **Unreal**: Press **Play** (Green Triangle).
5. **Terminal**: Activate `venv` and run your Python script.

---

## 4. Swarm Robotics (Multi-Drone)
Project AirSim supports controlling multiple vehicles simultaneously.

### Multi-Drone Example
```powershell
python two_drones.py
```

### Swarm Configuration
- **Template**: `client/python/example_user_scripts/sim_config/scene_two_drones.jsonc`
- **Tip**: Add more drone entries in the `robots` array to scale the swarm.

---

## 5. AI & Machine Learning Integration

### Synthetic Data Collection
- **Segmentation**: `python segmentation.py` (Color-coded object IDs)
- **LiDAR**: `python lidar_basic.py` (3D Point Cloud data)

### Reinforcement Learning (RL)
- **Gym Env**: `ProjectAirSimDetectAvoidEnv-v0`
- **Synchronous Mode**: Enabling the steppable clock is critical for RL training.
    - Reference: `client/python/example_user_scripts/clock_manual_step.py`

---

## 6. Development Tips
- **Coordinate System**: API uses **NED (North, East, Down)**. North is +X, East is +Y, Down is +Z.
- **Collision Settings**: For custom maps, set Collision Complexity to `Use Complex Collision as Simple`.
- **API Reference**: See `docs/api.md` for full command list.
