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

**Manual Control Test**: (If it goes wrong, try to run `pip install keyboard`)
```powershell
python keyboard_control.py
```

**Note**: Always stop the python script before stopping the unreal project.

---

## 3. Swarm Robotics (Multi-Drone)
Project AirSim supports controlling multiple vehicles simultaneously.

### Multi-Drone Example
```powershell
python two_drones.py
```

### Swarm Configuration
- **Template**: `client/python/example_user_scripts/sim_config/scene_two_drones.jsonc`
- **Tip**: Add more drone entries in the `robots` array to scale the swarm.

---

## 4. Advanced: Modifying Dynamics & Models

For those performing deep research into drone behavior, control algorithms, or new physics models, the following files are the primary entry points:

### Key Source Files
- **Physics Core**: [fast_physics.cpp](physics/src/fast_physics.cpp) - The main C++ motion engine ($F=ma$, Euler's equations, etc).
- **Robot Configuration**: [robot_quadrotor_fastphysics.jsonc](client/python/example_user_scripts/sim_config/robot_quadrotor_fastphysics.jsonc) - Physical parameters (mass, drag, thrust, etc).
- **Scene Setup**: [scene_basic_drone.jsonc](client/python/example_user_scripts/sim_config/scene_basic_drone.jsonc) - Environment and drone spawns.

### Physics & Tuning Guide
You can modify "Movement Models" and "Physical Properties" using JSONC files without needing to recompile.

#### A. Mass & Inertia
*   **Mass**: Found at `links[0].inertial.mass` (Unit: kg).
*   **Inertia**: Defined via the `body-box` geometry (affects rotation speed).

#### B. Aerodynamics
*   **Drag Coefficient**: Found in the `aerodynamics` section.
*   *Note: Increasing this lowers the top speed.*

#### C. Propulsion Model (Actuators)
In the `actuators` array:
*   **coeff-of-thrust**: Multiplier for lift. Increase to make the drone feel lighter.
*   **coeff-of-torque**: Determines yaw (turning) authority.
*   **max-rpm**: The limit of rotational motor speed.

#### D. Sensors & Data
The `sensors` array allows tuning:
*   **Camera**: Resolution, FOV, and Update Rate (`capture-interval`).
*   **IMU/GPS**: Noise levels and bias stability.

---
> [!IMPORTANT] \
> **To apply C++ changes**: If you edit `.cpp` files, you must run `.\build.cmd simlibs_debug` to recompile the DLLs before restarting Unreal.
