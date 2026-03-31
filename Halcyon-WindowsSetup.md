## TODO

- [ ] Follow the VSCode setup

## Getting Started

*Since we want to have a full control over the simulation, we would develop with Project AirSim source*
- Follow [Build From Source as a Developer](https://github.com/Nurassyl-lab/DroneSimDev/blob/main/docs/development/use_source.md#build-from-source-as-a-developer) for Linux
- Caution: [Developing Project AirSim Sim Libs](https://github.com/Nurassyl-lab/DroneSimDev/blob/main/docs/development/use_source.md#developing-project-airsim-sim-libs)


### Requirements:
[System Requirements](https://github.com/Nurassyl-lab/DroneSimDev/blob/main/docs/system_specs.md#installing-system-prerequisites)

- Windows 11
- NVIDIA GPU Drivers (verify by running `nvidia-smi`)
- Python version 3.9
- WSL running Ubuntu 24.04


### Unreal Engine Installation
- Download and install Launcher from [Unreal Engine website](https://www.unrealengine.com/en-US/download)
- Log in
- Install Unreal Engine version 5.7 
![Alt text](./attachments/unreal_engine_installation.png)


### Build AirSim
- Open "x64 Native Tools Command Prompt for VS 2022"
    - Run `cl`, if it shows "Microsoft (R) C/C++ Optimizing Compiler Version 19.44.35225 for x64" you're good to go
- `build.cmd all`

If successful you're ready to run a code:
1. (Recommended) create a python environment
2. Setup env using `./DroneSimDev/client/python/projectairsim/requirements.txt`
3. open `./DroneSimDev/unreal/Blocks/Blocks.uproject` in Unreal Engine Editor
4. Press play button (green triangle)
5. run a code `python ./DroneSimDev/client/python/example_user_scripts/hello_drone.py`
6. If you see Drone appear and move up&down, you're good

### Build PX4
1. in `./` run `https://github.com/PX4/PX4-Autopilot.git`
   1. `cd PX4-Autopilot`
2. (In WSL) create a python environment and run `pip install kconfiglib`
3. (In WSL) Run `make px4_sitl_default none_iris`
4. PX4 Should be running, Unreal Engine Editor should be playing, you're drone must be flying
    1. Play with script in `client/python/example_user_scripts`
5. Drone fly good, Drone no fly no good
