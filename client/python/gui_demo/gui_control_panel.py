#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DroneDigitalTwin & PX4 SITL GUI Control Panel
Created to automate starting Unreal Engine, PX4 SITL Docker, and Nura's Python client tools.
Uses gui_config.py for centralized configuration and dynamic path resolution.
"""

import os
import sys
import shutil
import subprocess
import threading
import queue
import time
import signal
import re
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Import path configurations from gui_config.py
from gui_config import (
    PROJECT_ROOT,
    VENV_PYTHON,
    GUI_DEMO_DIR,
    EXAMPLE_SCRIPTS_DIR,
    HALCYON_DEMO_DIR,
    DEFAULT_VIDEO_DIR,
    FLY_KEYBOARD_SH,
    UNREAL_EDITOR_PATH,
    PX4_AUTOPILOT_DIR,
    MAP_PROJECTS_DATA,
)


class DroneControlGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DroneDigitalTwin + PX4 SITL Control Panel")
        self.geometry("1080x820")
        self.minsize(900, 680)

        # Process management handles
        self.ue5_process = None
        self.active_script_process = None
        self.dashboard_process = None

        # State indicators
        self.is_ue5_running = False
        self.is_px4_running = False

        # Thread queue for UI log updates
        self.log_queue = queue.Queue()

        self._create_widgets()
        self._start_status_checker()
        self._process_log_queue()

    def _create_widgets(self):
        # Master Notebook dividing Control Panel & Console Log
        self.main_notebook = ctk.CTkTabview(self)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Control Panel
        self.panel_tab = self.main_notebook.add(" 🕹️ Control Panel ")

        # Tab 2: Console Log
        self.log_tab = self.main_notebook.add(" 📜 Console & Logs ")

        # -------------------------------------------------------------
        # Control Panel Top Controls
        # -------------------------------------------------------------
        self.top_frame = ctk.CTkFrame(self.panel_tab)
        self.top_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10), padx=5)

        top_title = ctk.CTkLabel(self.top_frame, text=" System & Simulation Environment Controls ", font=("TkDefaultFont", 12, "bold"))
        top_title.pack(anchor=tk.W, padx=10, pady=(5, 5))

        # Unreal Engine Controls
        ue_frame = ctk.CTkFrame(self.top_frame)
        ue_frame.pack(fill=tk.X, pady=4, padx=10)

        self.map_lbl = ctk.CTkLabel(ue_frame, text="Unreal Map: ", font=("TkDefaultFont", 10, "bold"))
        self.map_lbl.pack(side=tk.LEFT, padx=(5, 5))

        self.map_var = tk.StringVar()
        MAP_LABELS = {
            "map_river_forest": "LowPolyRiverForest (River & Forest Map)",
            "map_blocks": "Blocks (Default AirSim Map)",
            "map_walking_npcs": "WalkingNPCs (Truck & Pedestrians)",
        }
        self.map_labels_dict = MAP_LABELS
        map_options = [MAP_LABELS.get(key, key) for key, _ in MAP_PROJECTS_DATA]
        self.map_combo = ctk.CTkComboBox(ue_frame, variable=self.map_var, values=map_options, state="readonly", width=300)
        if map_options:
            self.map_combo.set(map_options[0])
        self.map_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.game_mode_var = tk.BooleanVar(value=True)
        self.game_mode_chk = ctk.CTkCheckBox(ue_frame, text="-game (Auto Play on Start)", variable=self.game_mode_var)
        self.game_mode_chk.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_launch_ue = ctk.CTkButton(ue_frame, text="▶ Launch Unreal Engine", command=self.launch_unreal)
        self.btn_launch_ue.pack(side=tk.LEFT, padx=3)

        self.btn_stop_ue = ctk.CTkButton(ue_frame, text="■ Stop Unreal", command=self.stop_unreal, fg_color="#C0392B", hover_color="#922B21")
        self.btn_stop_ue.pack(side=tk.LEFT, padx=3)

        self.ue_status_label = ctk.CTkLabel(ue_frame, text="● UE5: Checking...", text_color="gray", font=("TkDefaultFont", 10, "bold"))
        self.ue_status_label.pack(side=tk.LEFT, padx=(15, 0))

        # PX4 Container Controls
        px4_frame = ctk.CTkFrame(self.top_frame)
        px4_frame.pack(fill=tk.X, pady=(4, 8), padx=10)

        self.px4_lbl = ctk.CTkLabel(px4_frame, text="PX4 SITL Container: ", font=("TkDefaultFont", 10, "bold"))
        self.px4_lbl.pack(side=tk.LEFT, padx=(5, 5))

        self.btn_launch_px4 = ctk.CTkButton(px4_frame, text="▶ Launch PX4 SITL Container", command=self.launch_px4)
        self.btn_launch_px4.pack(side=tk.LEFT, padx=3)

        self.btn_stop_px4 = ctk.CTkButton(px4_frame, text="■ Stop PX4 Container", command=self.stop_px4, fg_color="#C0392B", hover_color="#922B21")
        self.btn_stop_px4.pack(side=tk.LEFT, padx=3)

        self.px4_status_label = ctk.CTkLabel(px4_frame, text="● PX4: Checking...", text_color="gray", font=("TkDefaultFont", 10, "bold"))
        self.px4_status_label.pack(side=tk.LEFT, padx=(15, 20))

        # Clean restart
        self.btn_clean_restart = ctk.CTkButton(px4_frame, text="🔄 Clean Restart UE5 + PX4", command=self.clean_restart_environment, fg_color="#D35400", hover_color="#A04000")
        self.btn_clean_restart.pack(side=tk.RIGHT, padx=5)

        # Sub-Notebook for Script Tools
        self.script_notebook = ctk.CTkTabview(self.panel_tab)
        self.script_notebook.pack(fill=tk.BOTH, expand=True)

        self._setup_tab_keyboard()
        self._setup_tab_astar()
        self._setup_tab_replan()
        self._setup_tab_fpv()
        self._setup_tab_cameras()
        self._setup_tab_map_viewer()
        self._setup_tab_assets()

        # Console Log tab
        log_bar = ctk.CTkFrame(self.log_tab)
        log_bar.pack(fill=tk.X, pady=(0, 8))

        self.script_status_label = ctk.CTkLabel(log_bar, text="● Current Task: Idle", font=("TkDefaultFont", 11, "bold"), text_color="green")
        self.script_status_label.pack(side=tk.LEFT, padx=5)

        self.btn_stop_script = ctk.CTkButton(log_bar, text="⛔ Terminate Current Python Task", command=self.stop_active_script, state="disabled", fg_color="#C0392B", hover_color="#922B21")
        self.btn_stop_script.pack(side=tk.RIGHT, padx=5)

        self.btn_clear_log = ctk.CTkButton(log_bar, text="🧹 Clear Log", command=self.clear_log)
        self.btn_clear_log.pack(side=tk.RIGHT, padx=5)

        # Log Text Box
        self.log_text = ctk.CTkTextbox(self.log_tab, font=("Monospace", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _ensure_dashboard_running(self):
        """Auto-launch telemetry dashboard window asynchronously if not already open."""
        if hasattr(self, "dashboard_process") and self.dashboard_process and self.dashboard_process.poll() is None:
            return
        cmd = [str(VENV_PYTHON), str(GUI_DEMO_DIR / "gui_dashboard.py")]
        try:
            self.dashboard_process = subprocess.Popen(cmd, cwd=GUI_DEMO_DIR)
            self.log("[SYSTEM] Auto-launched Telemetry Dashboard window.\n")
        except Exception as e:
            self.log(f"[ERROR] Failed to auto-launch Telemetry Dashboard: {e}\n")

    # -----------------------------------------------------------------
    # Helper: Check prerequisites before script runs
    # -----------------------------------------------------------------
    def _check_prerequisites(self, need_ue5=True, need_px4=False):
        if need_ue5 and not self.is_ue5_running:
            title = "Unreal Engine Not Detected"
            msg = "Unreal Engine is not running!\nScripts must connect to Unreal to execute.\n\nLaunch Unreal Engine now?"
            if messagebox.askyesno(title, msg):
                self.launch_unreal()
                time.sleep(2)
            else:
                return False

        if need_px4 and not self.is_px4_running:
            title = "PX4 SITL Container Not Detected"
            msg = "This feature requires PX4 SITL (TCP 4560 connection)!\nCurrently PX4 Container is not running.\n\nLaunch PX4 Container now?"
            if messagebox.askyesno(title, msg):
                self.launch_px4()
                time.sleep(2)
            else:
                return False

        return True

    # -----------------------------------------------------------------
    # Helper: Open interactive Terminal window with dynamic user/host prompt
    # -----------------------------------------------------------------
    def _run_cmd_in_terminal(self, cmd_args, cwd):
        self._ensure_dashboard_running()
        script_name = cmd_args[1] if len(cmd_args) > 1 else cmd_args[0]
        self.log(f"\n[TERMINAL EXEC] Launching {script_name} in new Terminal window...\n")
        cmd_parts = []
        for arg in cmd_args:
            if " " in arg or ";" in arg or '"' in arg:
                escaped = arg.replace('"', '\\"')
                cmd_parts.append(f'"{escaped}"')
            else:
                cmd_parts.append(arg)

        cmd_str = " ".join(cmd_parts)

        bash_cmd = (
            f'cd "{cwd}" && '
            f'read -e -p "$(whoami)@$(hostname):$(pwd)\\$ " -i "{cmd_str}" CMD && '
            f'eval "$CMD"; '
            f'exec bash'
        )

        terms = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]
        launched = False

        for term in terms:
            if shutil.which(term):
                try:
                    if term == "gnome-terminal":
                        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", bash_cmd])
                    elif term == "konsole":
                        subprocess.Popen(["konsole", "-e", "bash", "-c", bash_cmd])
                    elif term == "xfce4-terminal":
                        subprocess.Popen(["xfce4-terminal", "-e", f"bash -c \"{bash_cmd}\""])
                    elif term == "xterm":
                        subprocess.Popen(["xterm", "-e", f"bash -c \"{bash_cmd}\""])
                    launched = True
                    break
                except Exception:
                    continue

        if not launched:
            self.log(f"[NOTICE] No external GUI terminal emulator found. Executing task directly inside GUI console...\n")
            self._run_cmd_async(cmd_args, cwd)

    # -----------------------------------------------------------------
    # Tab 1: Keyboard Control
    # -----------------------------------------------------------------
    def _setup_tab_keyboard(self):
        tab = self.script_notebook.add(" ⌨️ Manual Flight ")

        self.kb_title_lbl = ctk.CTkLabel(tab, text="Keyboard Manual Flight Control (keyboard_control.py / truck2ped.py)", font=("TkDefaultFont", 11, "bold"))
        self.kb_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_mode = ctk.CTkFrame(tab)
        f_mode.pack(fill=tk.X, pady=5)
        self.kb_type_lbl = ctk.CTkLabel(f_mode, text="Select Script Type:")
        self.kb_type_lbl.pack(side=tk.LEFT, padx=(5, 10))
        self.kb_script_var = tk.StringVar(value="keyboard_control.py")
        self.kb_rb_basic = ctk.CTkRadioButton(f_mode, text="Basic Keyboard Flight (keyboard_control.py)", variable=self.kb_script_var, value="keyboard_control.py")
        self.kb_rb_basic.pack(side=tk.LEFT, padx=10)
        self.kb_rb_truck = ctk.CTkRadioButton(f_mode, text="Truck + Pedestrian Scene (truck2ped.py)", variable=self.kb_script_var, value="truck2ped.py")
        self.kb_rb_truck.pack(side=tk.LEFT, padx=10)

        f_px4 = ctk.CTkFrame(tab)
        f_px4.pack(fill=tk.X, pady=5)
        self.kb_use_px4_var = tk.BooleanVar(value=True)
        self.kb_chk_px4 = ctk.CTkCheckBox(f_px4, text="Use PX4 SITL Scene (scene_px4_sitl.jsonc)", variable=self.kb_use_px4_var)
        self.kb_chk_px4.pack(side=tk.LEFT, padx=5)

        f_start = ctk.CTkFrame(tab)
        f_start.pack(fill=tk.X, pady=5)
        self.kb_start_lbl = ctk.CTkLabel(f_start, text="Takeoff Position (--start x,y,z NED):")
        self.kb_start_lbl.pack(side=tk.LEFT, padx=(5, 10))
        self.kb_start_entry = ctk.CTkEntry(f_start, width=160)
        self.kb_start_entry.insert(0, "30,0,-6")
        self.kb_start_entry.pack(side=tk.LEFT)

        self.kb_info_box = ctk.CTkFrame(tab)
        self.kb_info_box.pack(fill=tk.X, pady=15, padx=5)
        info_title = ctk.CTkLabel(self.kb_info_box, text=" 💡 Linux Keyboard Control Notes ", font=("TkDefaultFont", 10, "bold"))
        info_title.pack(anchor=tk.W, padx=5, pady=(4, 2))
        info_msg = (
            "On Linux, the `keyboard` package requires root permissions to capture global hotkeys.\n"
            "1. Running directly inside GUI may not respond or give Permission Denied.\n"
            "2. Recommended: Click '💻 Launch Sudo Terminal' below to control WASD in a new window.\n"
            "3. If keys still don't respond under Chrome Remote Desktop, please use 'A* Autopilot'."
        )
        self.kb_info_lbl = ctk.CTkLabel(self.kb_info_box, text=info_msg, justify=tk.LEFT)
        self.kb_info_lbl.pack(anchor=tk.W, padx=10, pady=(0, 5))

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill=tk.X, pady=10)
        self.kb_btn_run = ctk.CTkButton(btn_frame, text="▶ Execute", command=self.run_keyboard_control)
        self.kb_btn_run.pack(side=tk.LEFT, padx=5)
        self.kb_btn_sudo = ctk.CTkButton(btn_frame, text="💻 Launch Sudo Terminal", command=self.run_keyboard_control_sudo)
        self.kb_btn_sudo.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 2: A* Autopilot
    # -----------------------------------------------------------------
    def _setup_tab_astar(self):
        tab = self.script_notebook.add(" 🧭 A* Autopilot ")

        self.astar_title_lbl = ctk.CTkLabel(tab, text="A* Path Planning & PX4 Autopilot (px4_astar_autopilot.py)", font=("TkDefaultFont", 11, "bold"))
        self.astar_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_preset = ctk.CTkFrame(tab)
        f_preset.pack(fill=tk.X, pady=5)
        self.astar_preset_lbl = ctk.CTkLabel(f_preset, text="Quick Preset Routes: ")
        self.astar_preset_lbl.pack(side=tk.LEFT, padx=(5, 5))

        preset_options = [
            "RiverForest Map - Short Route (72,-8,-4 -> 33,-19,-6)",
            "RiverForest Map - Long Route (72,-8,-4 -> -50,76,-25)",
            "Blocks Map - Standard Test (30,0,-6 -> 30,-48,-10)",
        ]
        self.astar_preset_combo = ctk.CTkComboBox(f_preset, values=preset_options, state="readonly", width=420)
        self.astar_preset_combo.set(preset_options[0])
        self.astar_preset_combo.pack(side=tk.LEFT, padx=5)
        self.astar_btn_preset = ctk.CTkButton(f_preset, text="Apply Preset", command=self.apply_astar_preset)
        self.astar_btn_preset.pack(side=tk.LEFT, padx=5)

        self.astar_form_frame = ctk.CTkFrame(tab)
        self.astar_form_frame.pack(fill=tk.X, pady=10, padx=5)
        self.astar_form_frame.columnconfigure(1, weight=1)
        self.astar_form_frame.columnconfigure(3, weight=1)

        form_title = ctk.CTkLabel(self.astar_form_frame, text=" Flight & Planning Parameters ", font=("TkDefaultFont", 10, "bold"))
        form_title.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=4)

        self.astar_entries = {}
        self.astar_label_refs = {}
        fields = [
            ("Start Position (--start):", "72,-8,-4", 1, 0, "start"),
            ("Goal Position (--goal):", "33,-19,-6", 1, 2, "goal"),
            ("Cruise Velocity m/s (--velocity-mps):", "2.0", 2, 0, "vel"),
            ("Accel Limit m/s² (--acceleration-limit-mps2):", "1.5", 2, 2, "acc"),
            ("Slowdown Dist m (--slowdown-distance-m):", "6.0", 3, 0, "slowdown"),
            ("Waypoint Acceptance m (--waypoint-acceptance-m):", "1.5", 3, 2, "accept"),
            ("Waypoint Hold Time sec (--waypoint-hold-sec):", "3.0", 4, 0, "hold"),
            ("Turn Yaw Rate dps (--path-yaw-rate-dps):", "10.0", 4, 2, "yaw_rate"),
            ("PX4 Timeout sec (--px4-ready-timeout-sec):", "300", 5, 0, "timeout"),
        ]

        for label_text, default_val, row, col, key in fields:
            lbl = ctk.CTkLabel(self.astar_form_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.astar_label_refs[key] = lbl

            entry = ctk.CTkEntry(self.astar_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.astar_entries[key] = entry

        chk_frame = ctk.CTkFrame(self.astar_form_frame)
        chk_frame.grid(row=6, column=0, columnspan=4, sticky=tk.W, pady=8, padx=5)

        self.astar_land_var = tk.BooleanVar(value=True)
        self.astar_land_chk = ctk.CTkCheckBox(chk_frame, text="Land at Goal (--land-at-goal)", variable=self.astar_land_var)
        self.astar_land_chk.pack(side=tk.LEFT, padx=8)

        self.astar_plan_only_var = tk.BooleanVar(value=False)
        self.astar_plan_chk = ctk.CTkCheckBox(chk_frame, text="Plan Only (No Flight) (--plan-only debug)", variable=self.astar_plan_only_var)
        self.astar_plan_chk.pack(side=tk.LEFT, padx=8)

        self.astar_print_wp_var = tk.BooleanVar(value=True)
        self.astar_print_chk = ctk.CTkCheckBox(chk_frame, text="Print Waypoints (--print-waypoints)", variable=self.astar_print_wp_var)
        self.astar_print_chk.pack(side=tk.LEFT, padx=8)

        self.astar_teleport_var = tk.BooleanVar(value=False)
        self.astar_teleport_chk = ctk.CTkCheckBox(chk_frame, text="Teleport to Start (--teleport-start)", variable=self.astar_teleport_var)
        self.astar_teleport_chk.pack(side=tk.LEFT, padx=8)

        self.astar_scene_origin_var = tk.BooleanVar(value=True)
        self.astar_origin_chk = ctk.CTkCheckBox(chk_frame, text="Set Start as Scene Origin (--start-as-scene-origin)", variable=self.astar_scene_origin_var)
        self.astar_origin_chk.pack(side=tk.LEFT, padx=8)

        btn_f = ctk.CTkFrame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.astar_btn_run = ctk.CTkButton(btn_f, text="▶ Execute", command=self.run_astar_autopilot)
        self.astar_btn_run.pack(side=tk.LEFT, padx=5)
        self.astar_btn_term = ctk.CTkButton(btn_f, text="💻 Terminal Execution", command=lambda: self.run_astar_autopilot(terminal_mode=True))
        self.astar_btn_term.pack(side=tk.LEFT, padx=5)

    def apply_astar_preset(self):
        val = self.astar_preset_combo.get()
        if "Short Route" in val:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "72,-8,-4")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "33,-19,-6")
            self.astar_scene_origin_var.set(True)
        elif "Long Route" in val:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "72,-8,-4")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "-50,76,-25")
            self.astar_scene_origin_var.set(True)
        else:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "30,0,-6")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "30,-48,-10")
            self.astar_scene_origin_var.set(False)

    # -----------------------------------------------------------------
    # Tab 3: Dynamic Re-planning
    # -----------------------------------------------------------------
    def _setup_tab_replan(self):
        tab = self.script_notebook.add(" ⚡ Dynamic Replanning ")

        self.replan_title_lbl = ctk.CTkLabel(tab, text="Dynamic Obstacle Avoidance & Path Replanning (route_replan_static.py)", font=("TkDefaultFont", 11, "bold"))
        self.replan_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_preset = ctk.CTkFrame(tab)
        f_preset.pack(fill=tk.X, pady=5)
        self.replan_preset_lbl = ctk.CTkLabel(f_preset, text="Quick Preset Routes: ")
        self.replan_preset_lbl.pack(side=tk.LEFT, padx=(5, 5))

        preset_options = [
            "RiverForest Map - Short Route (Direct Flight No Obstacle)",
            "RiverForest Map - Long Route (Dynamic Detour with Obstacles)",
        ]
        self.replan_preset_combo = ctk.CTkComboBox(f_preset, values=preset_options, state="readonly", width=450)
        self.replan_preset_combo.set(preset_options[0])
        self.replan_preset_combo.pack(side=tk.LEFT, padx=5)
        self.replan_btn_preset = ctk.CTkButton(f_preset, text="Apply Preset", command=self.apply_replan_preset)
        self.replan_btn_preset.pack(side=tk.LEFT, padx=5)

        self.replan_form_frame = ctk.CTkFrame(tab)
        self.replan_form_frame.pack(fill=tk.X, pady=10, padx=5)

        form_title = ctk.CTkLabel(self.replan_form_frame, text=" Avoidance & Flight Control Parameters ", font=("TkDefaultFont", 10, "bold"))
        form_title.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=4)

        self.replan_route_lbl = ctk.CTkLabel(self.replan_form_frame, text="Full Route Waypoints (--route N1;N2;...):")
        self.replan_route_lbl.grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        self.replan_route_entry = ctk.CTkEntry(self.replan_form_frame, width=600)
        self.replan_route_entry.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)

        self.replan_form_frame.columnconfigure(1, weight=1)
        self.replan_form_frame.columnconfigure(3, weight=1)

        self.replan_entries = {}
        self.replan_label_refs = {}
        fields = [
            ("Start Position (--start):", "72,-8.0,-4.0", 2, 0, "start"),
            ("Flight Driver (--flight-driver):", "velocity", 2, 2, "driver"),
            ("Obstacle Stop Distance m (--object-stop-distance-m):", "2.0", 3, 0, "stop_dist"),
            ("Emergency Detour Node (--replan-emergency-node):", "62.18,-0.41,-5.38", 3, 2, "emergency"),
            ("Rejoin Waypoint (--replan-rejoin-point):", "45.0,17.0,-16.0", 4, 0, "rejoin"),
            ("Velocity Lookahead m (--velocity-lookahead-m):", "8.0", 4, 2, "lookahead"),
            ("Turn Yaw Rate dps (--path-yaw-rate-dps):", "10.0", 5, 0, "yaw_rate"),
            ("Accel Limit m/s² (--acceleration-limit-mps2):", "1.0", 5, 2, "acc"),
        ]

        for label_text, default_val, row, col, key in fields:
            lbl = ctk.CTkLabel(self.replan_form_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.replan_label_refs[key] = lbl

            entry = ctk.CTkEntry(self.replan_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.replan_entries[key] = entry

        chk_frame = ctk.CTkFrame(self.replan_form_frame)
        chk_frame.grid(row=6, column=0, columnspan=4, sticky=tk.W, pady=8, padx=5)

        self.replan_on_object_var = tk.BooleanVar(value=True)
        self.replan_obj_chk = ctk.CTkCheckBox(chk_frame, text="Enable Auto Detour (--replan-on-object)", variable=self.replan_on_object_var)
        self.replan_obj_chk.pack(side=tk.LEFT, padx=8)

        self.replan_overlay_var = tk.BooleanVar(value=True)
        self.replan_overlay_chk = ctk.CTkCheckBox(chk_frame, text="Enable 3rd-Person Chase Cam Overlay (--third-person-overlay)", variable=self.replan_overlay_var)
        self.replan_overlay_chk.pack(side=tk.LEFT, padx=8)

        self.replan_origin_var = tk.BooleanVar(value=True)
        self.replan_origin_chk = ctk.CTkCheckBox(chk_frame, text="Set Start as Scene Origin (--start-as-scene-origin)", variable=self.replan_origin_var)
        self.replan_origin_chk.pack(side=tk.LEFT, padx=8)

        self.apply_replan_preset()

        btn_f = ctk.CTkFrame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.replan_btn_run = ctk.CTkButton(btn_f, text="▶ Execute", command=self.run_replan_static)
        self.replan_btn_run.pack(side=tk.LEFT, padx=5)
        self.replan_btn_term = ctk.CTkButton(btn_f, text="💻 Terminal Execution", command=lambda: self.run_replan_static(terminal_mode=True))
        self.replan_btn_term.pack(side=tk.LEFT, padx=5)

    def apply_replan_preset(self):
        val = self.replan_preset_combo.get()
        if "Short Route" in val:
            route_str = "72,-8,-4; 69,-10,-40; 66,-11,-40; 63,-11,-40; 60,-12,-40; 57,-12,-40; 54,-12,-40; 51,-12,-40; 48,-12,-40; 45,-13,-40; 42,-13,-40; 39,-16,-40; 36,-17,-40; 33,-19,-6"
            self.replan_route_entry.delete(0, tk.END); self.replan_route_entry.insert(0, route_str)
            self.replan_entries["start"].delete(0, tk.END); self.replan_entries["start"].insert(0, "72,-8,-4")
        else:
            route_str = "72.0,-8.0,-4.0; 69.93,-5.19,-5.36; 66.98,1.81,-4.61; 64.38,6.0,-4.00; 61.0,10.0,-4.5; 58.0,14.0,-5.0; 55.0,18.0,-5.5; 45.0,17.0,-16.0; 28.0,25.0,-24.0; 13.0,39.0,-24.0; -2.0,54.0,-27.0; -17.0,69.0,-27.0; -38.0,72.0,-28.0; -50.0,76.0,-25.0"
            self.replan_route_entry.delete(0, tk.END); self.replan_route_entry.insert(0, route_str)
            self.replan_entries["start"].delete(0, tk.END); self.replan_entries["start"].insert(0, "72,-8.0,-4.0")

    # -----------------------------------------------------------------
    # Tab 4: FPV Overlay & Video
    # -----------------------------------------------------------------
    def _setup_tab_fpv(self):
        tab = self.script_notebook.add(" 📹 FPV Overlay ")

        self.fpv_title_lbl = ctk.CTkLabel(tab, text="FPV First Person View Path Overlay & Video Recording (fpv_route_overlay.py)", font=("TkDefaultFont", 11, "bold"))
        self.fpv_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.fpv_info_box = ctk.CTkFrame(tab)
        self.fpv_info_box.pack(fill=tk.X, pady=(0, 10), padx=5)
        info_title = ctk.CTkLabel(self.fpv_info_box, text=" 💡 What is FPV Path Overlay & Recording? ", font=("TkDefaultFont", 10, "bold"))
        info_title.pack(anchor=tk.W, padx=5, pady=(4, 2))
        info_msg = (
            "FPV overlay guides the drone along A* waypoints while projecting 3D path points onto front camera:\n"
            "• Visual effect: Passed/active waypoints highlight in green (like HUD / flight navigation rings).\n"
            "• Video Output: Records full flight overlay into MP4 video (default: DroneDigitalTwin/video/).\n"
            "⚠️ Prerequisite: Unreal Engine and PX4 SITL Container must be running!"
        )
        self.fpv_info_lbl = ctk.CTkLabel(self.fpv_info_box, text=info_msg, justify=tk.LEFT)
        self.fpv_info_lbl.pack(anchor=tk.W, padx=10, pady=(0, 5))

        self.fpv_form_frame = ctk.CTkFrame(tab)
        self.fpv_form_frame.pack(fill=tk.X, pady=10, padx=5)
        self.fpv_form_frame.columnconfigure(1, weight=1)
        self.fpv_form_frame.columnconfigure(3, weight=1)

        form_title = ctk.CTkLabel(self.fpv_form_frame, text=" Overlay & Video Settings ", font=("TkDefaultFont", 10, "bold"))
        form_title.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=4)

        self.fpv_entries = {}
        self.fpv_label_refs = {}
        fields = [
            ("Start Position (--start):", "72,-8,-4", 1, 0, "start"),
            ("Goal Position (--goal):", "-50, 76, -25", 1, 2, "goal"),
            ("Front Camera Pitch Angle (--front-rgb-angle):", "25", 2, 0, "angle"),
            ("Waypoint Distance m (--waypoint-distance-m):", "30", 2, 2, "wp_dist"),
            ("Min Flight Altitude m (--min-altitude):", "32", 3, 0, "min_alt"),
            ("Flight Speed m/s (--velocity-mps):", "3.0", 3, 2, "vel"),
            ("Video Output Directory (--video-path):", DEFAULT_VIDEO_DIR, 4, 0, "v_path"),
            ("Preview Resolution [WxH]:", "1920x1080", 4, 2, "res"),
        ]

        for label_text, default_val, row, col, key in fields:
            lbl = ctk.CTkLabel(self.fpv_form_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.fpv_label_refs[key] = lbl

            entry = ctk.CTkEntry(self.fpv_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.fpv_entries[key] = entry

        self.fpv_scene_origin_var = tk.BooleanVar(value=True)
        self.fpv_origin_chk = ctk.CTkCheckBox(self.fpv_form_frame, text="Set Start as Scene Origin (--start-as-scene-origin)", variable=self.fpv_scene_origin_var)
        self.fpv_origin_chk.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=8, padx=5)

        btn_f = ctk.CTkFrame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.fpv_btn_run = ctk.CTkButton(btn_f, text="▶ Execute", command=self.run_fpv_overlay)
        self.fpv_btn_run.pack(side=tk.LEFT, padx=5)
        self.fpv_btn_term = ctk.CTkButton(btn_f, text="💻 Terminal Execution", command=lambda: self.run_fpv_overlay(terminal_mode=True))
        self.fpv_btn_term.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 5: Camera & Sensor Test
    # -----------------------------------------------------------------
    def _setup_tab_cameras(self):
        tab = self.script_notebook.add(" 📷 Camera & Sensors ")

        self.cam_title_lbl = ctk.CTkLabel(tab, text="Onboard Cameras & LiDAR Testbench (check_all_cameras.py)", font=("TkDefaultFont", 11, "bold"))
        self.cam_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.cam_info_box = ctk.CTkFrame(tab)
        self.cam_info_box.pack(fill=tk.X, pady=(0, 10), padx=5)
        info_title = ctk.CTkLabel(self.cam_info_box, text=" 💡 What is Camera & Sensor Test? ", font=("TkDefaultFont", 10, "bold"))
        info_title.pack(anchor=tk.W, padx=5, pady=(4, 2))
        info_msg = (
            "Displays OpenCV real-time preview windows showing current camera feeds:\n"
            "• RGB Cameras (Front/Left/Right/Down): Verify aerial view & visual detection.\n"
            "• Depth Camera: Colorized depth map (brighter = closer) for obstacle distance testing.\n"
            "• LiDAR: 3D point cloud & forward high-density scan (dense-forward) for radar verification.\n"
            "⚠️ Tip: Must start Unreal Engine & click Play before OpenCV windows pop up!"
        )
        self.cam_info_lbl = ctk.CTkLabel(self.cam_info_box, text=info_msg, justify=tk.LEFT)
        self.cam_info_lbl.pack(anchor=tk.W, padx=10, pady=(0, 5))

        self.cam_form_frame = ctk.CTkFrame(tab)
        self.cam_form_frame.pack(fill=tk.X, pady=10, padx=5)
        self.cam_form_frame.columnconfigure(1, weight=1)
        self.cam_form_frame.columnconfigure(3, weight=1)

        form_title = ctk.CTkLabel(self.cam_form_frame, text=" Sensor Test Settings ", font=("TkDefaultFont", 10, "bold"))
        form_title.grid(row=0, column=0, columnspan=4, sticky=tk.W, padx=5, pady=4)

        self.cam_type_lbl = ctk.CTkLabel(self.cam_form_frame, text="Test Camera Type (--camera):")
        self.cam_type_lbl.grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)

        self.cam_type_var = tk.StringVar(value="all")
        cam_combo = ctk.CTkComboBox(self.cam_form_frame, variable=self.cam_type_var, values=["all", "rgb", "depth", "lidar"], state="readonly")
        cam_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=4)

        self.cam_lidar_lbl = ctk.CTkLabel(self.cam_form_frame, text="LiDAR Quality Preset (--lidar-quality-preset):")
        self.cam_lidar_lbl.grid(row=1, column=2, sticky=tk.W, padx=5, pady=4)

        self.lidar_preset_var = tk.StringVar(value="dense-forward")
        lidar_combo = ctk.CTkComboBox(self.cam_form_frame, variable=self.lidar_preset_var, values=["dense-forward", "default", "sparse"], state="readonly")
        lidar_combo.grid(row=1, column=3, sticky=tk.EW, padx=5, pady=4)

        self.cam_entries = {}
        self.cam_label_refs = {}
        fields = [
            ("Depth Min Distance m (--depth-min-m):", "0.1", 2, 0, "d_min"),
            ("Depth Max Distance m (--depth-max-m):", "80.0", 2, 2, "d_max"),
            ("Front RGB Angle (--front-rgb-angle):", "25", 3, 0, "rgb_ang"),
            ("Depth Camera Angle (--depth-angle):", "25", 3, 2, "dep_ang"),
            ("Start Position (--start):", "0,0,-28", 4, 0, "start"),
        ]

        for label_text, default_val, row, col, key in fields:
            lbl = ctk.CTkLabel(self.cam_form_frame, text=label_text)
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.cam_label_refs[key] = lbl

            entry = ctk.CTkEntry(self.cam_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.cam_entries[key] = entry

        chk_frame = ctk.CTkFrame(self.cam_form_frame)
        chk_frame.grid(row=5, column=0, columnspan=4, sticky=tk.W, pady=8, padx=5)

        self.cam_fly_pattern_var = tk.BooleanVar(value=True)
        self.cam_fly_chk = ctk.CTkCheckBox(chk_frame, text="Auto Test Flight Route (--fly-pattern)", variable=self.cam_fly_pattern_var)
        self.cam_fly_chk.pack(side=tk.LEFT, padx=8)

        self.cam_avoid_var = tk.BooleanVar(value=True)
        self.cam_avoid_chk = ctk.CTkCheckBox(chk_frame, text="Enable Obstacle Avoidance (--avoid-obstacles)", variable=self.cam_avoid_var)
        self.cam_avoid_chk.pack(side=tk.LEFT, padx=8)

        self.cam_teleport_var = tk.BooleanVar(value=True)
        self.cam_teleport_chk = ctk.CTkCheckBox(chk_frame, text="Teleport to Start (--teleport-start)", variable=self.cam_teleport_var)
        self.cam_teleport_chk.pack(side=tk.LEFT, padx=8)

        btn_f = ctk.CTkFrame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.cam_btn_run = ctk.CTkButton(btn_f, text="▶ Execute", command=self.run_check_cameras)
        self.cam_btn_run.pack(side=tk.LEFT, padx=5)
        self.cam_btn_term = ctk.CTkButton(btn_f, text="💻 Terminal Execution", command=lambda: self.run_check_cameras(terminal_mode=True))
        self.cam_btn_term.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 6: Map Viewer & Scanning
    # -----------------------------------------------------------------
    def _setup_tab_map_viewer(self):
        tab = self.script_notebook.add(" 🗺️ Map Scanner ")

        self.map_title_lbl = ctk.CTkLabel(tab, text="Scene Obstacle Scan & 2D/3D Occupancy Grid Generation (px4_map_viewer.py)", font=("TkDefaultFont", 11, "bold"))
        self.map_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.map_info_box = ctk.CTkFrame(tab)
        self.map_info_box.pack(fill=tk.X, pady=(0, 10), padx=5)
        info_title = ctk.CTkLabel(self.map_info_box, text=" 💡 What is Map Scanning & Occupancy Grid? ", font=("TkDefaultFont", 10, "bold"))
        info_title.pack(anchor=tk.W, padx=5, pady=(4, 2))
        info_msg = (
            "Scans terrain, trees, and buildings via Unreal raycasting without flying the drone:\n"
            "• Slices at specified Z altitude (e.g. -8.0m) to generate 2D/3D occupancy maps.\n"
            "• Core Purpose: Used by A* Autopilot (px4_astar_autopilot.py) to compute collision-free routes.\n"
            "⚠️ Tip: Must start Unreal Engine & click Play before scanning!"
        )
        self.map_info_lbl = ctk.CTkLabel(self.map_info_box, text=info_msg, justify=tk.LEFT)
        self.map_info_lbl.pack(anchor=tk.W, padx=10, pady=(0, 5))

        top_split = ctk.CTkFrame(tab)
        top_split.pack(fill=tk.BOTH, expand=True)

        self.map_form_frame = ctk.CTkFrame(top_split)
        self.map_form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)

        form_title = ctk.CTkLabel(self.map_form_frame, text=" Scanning Settings ", font=("TkDefaultFont", 10, "bold"))
        form_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=4)

        self.map_entries = {}
        self.map_label_refs = {}
        fields = [
            ("Scan Start (--start):", "40,-20,-6", "start"),
            ("Scan Goal (--goal):", "50,20,-6", "goal"),
            ("Z-Axis Slice Altitude (--slice-z-ned):", "-8.0", "slice_z"),
            ("Resolution m (--resolution-m):", "1.0", "res"),
            ("Map Bounds m (--map-size):", "500,500,10", "size"),
            ("2D Image Output (--output):", "riverside_forest.png", "out_2d"),
            ("3D Image Output (--output-3d):", "riverside_forest_3d.png", "out_3d"),
        ]

        for i, (label_text, default_val, key) in enumerate(fields):
            lbl = ctk.CTkLabel(self.map_form_frame, text=label_text)
            lbl.grid(row=i+1, column=0, sticky=tk.W, padx=5, pady=4)
            self.map_label_refs[key] = lbl

            entry = ctk.CTkEntry(self.map_form_frame, width=180)
            entry.insert(0, default_val)
            entry.grid(row=i+1, column=1, sticky=tk.EW, padx=5, pady=4)
            self.map_entries[key] = entry

        btn_f = ctk.CTkFrame(self.map_form_frame)
        btn_f.grid(row=len(fields)+1, column=0, columnspan=2, pady=15)
        self.map_btn_scan = ctk.CTkButton(btn_f, text="🗺️ Start Scan & Display PNG", command=self.run_map_viewer)
        self.map_btn_scan.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.map_btn_term = ctk.CTkButton(btn_f, text="💻 Terminal Execution", command=lambda: self.run_map_viewer(terminal_mode=True))
        self.map_btn_term.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.map_img_frame = ctk.CTkFrame(top_split)
        self.map_img_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)

        img_title = ctk.CTkLabel(self.map_img_frame, text=" Occupancy Grid Preview (PNG View) ", font=("TkDefaultFont", 10, "bold"))
        img_title.pack(anchor=tk.W, padx=5, pady=(4, 2))

        self.img_label = ctk.CTkLabel(self.map_img_frame, text="Click 'Start Scan' to generate and view 2D/3D occupancy map", anchor=tk.CENTER)
        self.img_label.pack(fill=tk.BOTH, expand=True)

    def display_map_image(self, image_path):
        try:
            if not os.path.exists(image_path):
                return
            img = Image.open(image_path)
            img.thumbnail((450, 400))
            photo = ImageTk.PhotoImage(img)
            self.img_label.configure(image=photo, text="")
            self.img_label.image = photo
        except Exception as e:
            self.log(f"Cannot load image {image_path}: {e}\n")

    # -----------------------------------------------------------------
    # Tab 7: Assets Query
    # -----------------------------------------------------------------
    def _setup_tab_assets(self):
        tab = self.script_notebook.add(" 🔍 Asset Inspector ")

        self.asset_title_lbl = ctk.CTkLabel(tab, text="Inspect Spawnable Asset IDs in Scene (list_spawnable_assets.py)", font=("TkDefaultFont", 11, "bold"))
        self.asset_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_query = ctk.CTkFrame(tab)
        f_query.pack(fill=tk.X, pady=5)
        self.asset_regex_lbl = ctk.CTkLabel(f_query, text="Asset Keyword / Regex (--asset-regex):")
        self.asset_regex_lbl.pack(side=tk.LEFT, padx=(5, 10))
        self.asset_regex_entry = ctk.CTkEntry(f_query, width=200)
        self.asset_regex_entry.insert(0, ".*Tree.*")
        self.asset_regex_entry.pack(side=tk.LEFT, padx=5)

        self.asset_btn_query = ctk.CTkButton(f_query, text="🔍 Query Assets", command=self.run_list_assets)
        self.asset_btn_query.pack(side=tk.LEFT, padx=5)
        self.asset_btn_term = ctk.CTkButton(f_query, text="💻 Terminal Execution", command=lambda: self.run_list_assets(terminal_mode=True))
        self.asset_btn_term.pack(side=tk.LEFT, padx=5)

        self.asset_res_frame = ctk.CTkFrame(tab)
        self.asset_res_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)

        res_title = ctk.CTkLabel(self.asset_res_frame, text=" Query Results ", font=("TkDefaultFont", 10, "bold"))
        res_title.pack(anchor=tk.W, padx=5, pady=(4, 2))

        self.asset_text = ctk.CTkTextbox(self.asset_res_frame, font=("Monospace", 10))
        self.asset_text.pack(fill=tk.BOTH, expand=True)

    # =================================================================
    # Process Execution & Thread Management
    # =================================================================
    def log(self, text):
        self.log_queue.put(text)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, msg)
            self.log_text.see(tk.END)
        self.after(100, self._process_log_queue)

    def _run_cmd_async(self, cmd_args, cwd, on_finish_callback=None):
        if self.active_script_process and self.active_script_process.poll() is None:
            messagebox.showwarning("Warning", "A Python script is already running! Please stop the current task first.")
            return

        self._ensure_dashboard_running()

        env = os.environ.copy()
        env["PATH"] = f"{VENV_PYTHON.parent}:{env.get('PATH', '')}"

        self.log(f"\n[EXEC] cwd={cwd}\n[CMD] {' '.join(cmd_args)}\n\n")
        script_label = cmd_args[1] if len(cmd_args)>1 else cmd_args[0]
        self.script_status_label.configure(text=f"● Current Task: Running ({script_label})", text_color="#007acc")
        self.btn_stop_script.configure(state="normal")

        self.main_notebook.set(" 📜 Console & Logs ")

        def runner():
            try:
                self.active_script_process = subprocess.Popen(
                    cmd_args,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in iter(self.active_script_process.stdout.readline, ''):
                    if line:
                        self.log(line)

                self.active_script_process.wait()
                rc = self.active_script_process.returncode
                self.log(f"\n[FINISHED] Process exited with code {rc}\n")
            except Exception as e:
                self.log(f"\n[ERROR] Process failed: {e}\n")
            finally:
                self.active_script_process = None
                self.after(0, lambda: self.script_status_label.configure(text="● Current Task: Idle", text_color="green"))
                self.after(0, lambda: self.btn_stop_script.configure(state="disabled"))
                if on_finish_callback:
                    self.after(0, on_finish_callback)

        threading.Thread(target=runner, daemon=True).start()

    def stop_active_script(self):
        if self.active_script_process and self.active_script_process.poll() is None:
            self.log("\n[ACTION] Terminating active task...\n")
            try:
                self.active_script_process.terminate()
                time.sleep(0.5)
                if self.active_script_process.poll() is None:
                    self.active_script_process.kill()
            except Exception as e:
                self.log(f"[ERROR] Termination failed: {e}\n")

    # =================================================================
    # System Launchers: UE5 & PX4
    # =================================================================
    def launch_unreal(self):
        map_display = self.map_combo.get()
        project_path = MAP_PROJECTS_DATA[0][1]
        for key, path in MAP_PROJECTS_DATA:
            if getattr(self, 'map_labels_dict', {}).get(key, key) == map_display:
                project_path = path
                break

        cmd = [str(UNREAL_EDITOR_PATH), str(project_path), "-ResX=1280", "-ResY=720", "-WINDOWED"]
        if self.game_mode_var.get():
            cmd.append("-game")

        self.log(f"\n[SYSTEM] Launching Unreal Engine 5: {map_display}\n")
        try:
            self.ue5_process = subprocess.Popen(cmd)
            self.log(f"[SYSTEM] Unreal Engine PID: {self.ue5_process.pid}\n")
            self.ue_status_label.configure(text="● UE5: Starting...", text_color="orange")
        except Exception as e:
            self.log(f"[ERROR] Launching Unreal Engine failed: {e}\n")
            messagebox.showerror("Error", f"Launch Unreal Engine failed:\n{e}")

    def stop_unreal(self):
        self.log("\n[SYSTEM] Killing Unreal Engine processes...\n")
        subprocess.run(["pkill", "-9", "-f", "UnrealEditor"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "Blocks.uproject"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "ForestDomeEnv.uproject"], capture_output=True)
        self.ue5_process = None
        self.is_ue5_running = False
        self.ue_status_label.configure(text="● UE5: Stopped", text_color="red")

    def launch_px4(self):
        self.log("\n[SYSTEM] Launching PX4 SITL Docker Container...\n")
        cmd = [
            "docker", "run", "--rm", "-d",
            "--name", "px4_sitl_gui_container",
            "--privileged", "--network", "host",
            "-v", f"{PX4_AUTOPILOT_DIR}:/src/PX4-Autopilot:rw",
            "-w", "/src/PX4-Autopilot",
            "px4io/px4-dev-simulation-jammy",
            "bash", "-c", "git config --global --add safe.directory '*' && make px4_sitl_default none_iris"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.log("[SYSTEM] PX4 SITL Docker container launched in background!\n")
                self.px4_status_label.configure(text="● PX4 Container: Starting...", text_color="orange")
            else:
                self.log(f"[ERROR] Launching PX4 container failed: {res.stderr}\n")
        except Exception as e:
            self.log(f"[ERROR] PX4 container execution error: {e}\n")

    def stop_px4(self):
        self.log("\n[SYSTEM] Stopping PX4 Docker Container...\n")
        subprocess.run(["docker", "stop", "px4_sitl_gui_container"], capture_output=True)
        self.is_px4_running = False
        self.px4_status_label.configure(text="● PX4 Container: Stopped", text_color="red")

    def clean_restart_environment(self):
        title = "Clean Restart"
        msg = "This will forcefully stop Unreal Engine and PX4 Container to free TCP port 4560. Proceed?"
        if messagebox.askyesno(title, msg):
            self.log("\n[RESTART] Cleaning up & restarting environment...\n")
            self.stop_active_script()
            self.stop_px4()
            self.stop_unreal()
            time.sleep(2)
            self.launch_unreal()
            time.sleep(3)
            self.launch_px4()
            self.log("[RESTART] Restart commands sent!\n")

    def _start_status_checker(self):
        def check_loop():
            while True:
                ue_running = False
                res_ue = subprocess.run(["pgrep", "-f", "UnrealEditor"], capture_output=True)
                if res_ue.returncode == 0 and res_ue.stdout.strip():
                    ue_running = True

                px4_running = False
                res_px4 = subprocess.run(["docker", "ps", "-q", "-f", "name=px4_sitl_gui_container"], capture_output=True, text=True)
                if res_px4.returncode == 0 and res_px4.stdout.strip():
                    px4_running = True

                self.is_ue5_running = ue_running
                self.is_px4_running = px4_running

                self.after(0, lambda r1=ue_running, r2=px4_running: self._update_status_ui(r1, r2))
                time.sleep(3)

        threading.Thread(target=check_loop, daemon=True).start()

    def _update_status_ui(self, ue_running, px4_running):
        if ue_running:
            self.ue_status_label.configure(text="● UE5: Running", text_color="green")
        else:
            self.ue_status_label.configure(text="● UE5: Stopped", text_color="red")

        if px4_running:
            self.px4_status_label.configure(text="● PX4 Container: Running", text_color="green")
        else:
            self.px4_status_label.configure(text="● PX4 Container: Stopped", text_color="red")

    # =================================================================
    # Client Script Actions
    # =================================================================
    def run_keyboard_control(self):
        if not self._check_prerequisites(need_ue5=True, need_px4=self.kb_use_px4_var.get()):
            return

        script_name = self.kb_script_var.get()
        cwd = HALCYON_DEMO_DIR if script_name == "truck2ped.py" else EXAMPLE_SCRIPTS_DIR
        cmd = [str(VENV_PYTHON), script_name]

        if self.kb_use_px4_var.get() and script_name == "keyboard_control.py":
            cmd.extend(["--sceneconfigfile", "scene_px4_sitl.jsonc"])

        start_val = self.kb_start_entry.get().strip()
        if start_val:
            cmd.extend(["--start", start_val])

        self._run_cmd_async(cmd, cwd)

    def run_keyboard_control_sudo(self):
        if not self._check_prerequisites(need_ue5=True, need_px4=True):
            return

        self._ensure_dashboard_running()
        script_path = FLY_KEYBOARD_SH
        self.log("\n[SYSTEM] Opening Terminal window with Sudo to run fly_keyboard.sh...\n")
        self.main_notebook.select(self.log_tab)

        term_cmd = f"sudo {script_path}; read -p 'Press Enter to close window...'"
        cmd = ["gnome-terminal", "--", "bash", "-c", term_cmd]
        try:
            subprocess.Popen(cmd)
        except Exception:
            try:
                subprocess.Popen(["xterm", "-e", f"bash -c \"{term_cmd}\""])
            except Exception as e:
                self.log(f"[ERROR] Cannot open Terminal window: {e}\n")

    def run_astar_autopilot(self, terminal_mode=False):
        need_px4 = not self.astar_plan_only_var.get()
        if not self._check_prerequisites(need_ue5=True, need_px4=need_px4):
            return

        cmd = [str(VENV_PYTHON), "px4_astar_autopilot.py"]

        start = self.astar_entries["start"].get().strip()
        goal = self.astar_entries["goal"].get().strip()
        if start: cmd.extend(["--start", start])
        if goal: cmd.extend(["--goal", goal])

        cmd.extend(["--velocity-mps", self.astar_entries["vel"].get().strip()])
        cmd.extend(["--acceleration-limit-mps2", self.astar_entries["acc"].get().strip()])
        cmd.extend(["--slowdown-distance-m", self.astar_entries["slowdown"].get().strip()])
        cmd.extend(["--waypoint-acceptance-m", self.astar_entries["accept"].get().strip()])
        cmd.extend(["--waypoint-hold-sec", self.astar_entries["hold"].get().strip()])
        cmd.extend(["--path-yaw-rate-dps", self.astar_entries["yaw_rate"].get().strip()])
        cmd.extend(["--px4-ready-timeout-sec", self.astar_entries["timeout"].get().strip()])

        if self.astar_land_var.get(): cmd.append("--land-at-goal")
        if self.astar_plan_only_var.get(): cmd.append("--plan-only")
        if self.astar_print_wp_var.get(): cmd.append("--print-waypoints")
        if self.astar_teleport_var.get(): cmd.append("--teleport-start")
        if self.astar_scene_origin_var.get(): cmd.append("--start-as-scene-origin")

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, EXAMPLE_SCRIPTS_DIR)
        else:
            self._run_cmd_async(cmd, EXAMPLE_SCRIPTS_DIR)

    def run_replan_static(self, terminal_mode=False):
        if not self._check_prerequisites(need_ue5=True, need_px4=True):
            return

        cmd = [str(VENV_PYTHON), "route_replan_static.py"]

        route = self.replan_route_entry.get().strip()
        if route: cmd.extend(["--route", route])

        cmd.extend(["--start", self.replan_entries["start"].get().strip()])
        cmd.extend(["--flight-driver", self.replan_entries["driver"].get().strip()])
        cmd.extend(["--object-stop-distance-m", self.replan_entries["stop_dist"].get().strip()])
        cmd.extend(["--replan-emergency-node", self.replan_entries["emergency"].get().strip()])
        cmd.extend(["--replan-rejoin-point", self.replan_entries["rejoin"].get().strip()])
        cmd.extend(["--velocity-lookahead-m", self.replan_entries["lookahead"].get().strip()])
        cmd.extend(["--path-yaw-rate-dps", self.replan_entries["yaw_rate"].get().strip()])
        cmd.extend(["--acceleration-limit-mps2", self.replan_entries["acc"].get().strip()])

        if self.replan_on_object_var.get():
            cmd.append("--replan-on-object")
        else:
            cmd.append("--no-replan-on-object")

        if self.replan_overlay_var.get():
            cmd.extend(["--third-person-overlay", "--third-person-camera", "chase"])

        if self.replan_origin_var.get():
            cmd.append("--start-as-scene-origin")

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, HALCYON_DEMO_DIR)
        else:
            self._run_cmd_async(cmd, HALCYON_DEMO_DIR)

    def run_fpv_overlay(self, terminal_mode=False):
        if not self._check_prerequisites(need_ue5=True, need_px4=True):
            return

        cmd = [str(VENV_PYTHON), "fpv_route_overlay.py"]

        cmd.extend(["--start", self.fpv_entries["start"].get().strip()])
        cmd.extend(["--goal", self.fpv_entries["goal"].get().strip()])
        cmd.extend(["--front-rgb-angle", self.fpv_entries["angle"].get().strip()])
        cmd.extend(["--waypoint-distance-m", self.fpv_entries["wp_dist"].get().strip()])
        cmd.extend(["--min-altitude", self.fpv_entries["min_alt"].get().strip()])
        cmd.extend(["--velocity-mps", self.fpv_entries["vel"].get().strip()])

        v_path = self.fpv_entries["v_path"].get().strip()
        if v_path:
            os.makedirs(v_path, exist_ok=True)
            cmd.extend(["--video-path", v_path])

        wh = self.fpv_entries["res"].get().strip().split("x")
        if len(wh) == 2:
            cmd.extend(["--preview-width", wh[0], "--preview-height", wh[1]])

        if self.fpv_scene_origin_var.get():
            cmd.append("--start-as-scene-origin")

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, EXAMPLE_SCRIPTS_DIR)
        else:
            self._run_cmd_async(cmd, EXAMPLE_SCRIPTS_DIR)

    def run_check_cameras(self, terminal_mode=False):
        if not self._check_prerequisites(need_ue5=True, need_px4=False):
            return

        cmd = [str(VENV_PYTHON), "check_all_cameras.py"]

        cmd.extend(["--camera", self.cam_type_var.get()])
        cmd.extend(["--lidar-quality-preset", self.lidar_preset_var.get()])
        cmd.extend(["--depth-min-m", self.cam_entries["d_min"].get().strip()])
        cmd.extend(["--depth-max-m", self.cam_entries["d_max"].get().strip()])
        cmd.extend(["--front-rgb-angle", self.cam_entries["rgb_ang"].get().strip()])
        cmd.extend(["--depth-angle", self.cam_entries["dep_ang"].get().strip()])
        cmd.extend(["--start", self.cam_entries["start"].get().strip()])

        if self.cam_fly_pattern_var.get(): cmd.append("--fly-pattern")
        if self.cam_avoid_var.get(): cmd.append("--avoid-obstacles")
        if self.cam_teleport_var.get(): cmd.append("--teleport-start")

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, EXAMPLE_SCRIPTS_DIR)
        else:
            self._run_cmd_async(cmd, EXAMPLE_SCRIPTS_DIR)

    def run_map_viewer(self, terminal_mode=False):
        if not self._check_prerequisites(need_ue5=True, need_px4=False):
            return

        cmd = [str(VENV_PYTHON), "px4_map_viewer.py"]

        cmd.extend(["--start", self.map_entries["start"].get().strip()])
        cmd.extend(["--goal", self.map_entries["goal"].get().strip()])
        cmd.extend(["--slice-z-ned", self.map_entries["slice_z"].get().strip()])
        cmd.extend(["--resolution-m", self.map_entries["res"].get().strip()])
        cmd.extend(["--map-size", self.map_entries["size"].get().strip()])

        out_2d = self.map_entries["out_2d"].get().strip()
        out_3d = self.map_entries["out_3d"].get().strip()
        cmd.extend(["--output", out_2d, "--output-3d", out_3d])

        out_2d_full = EXAMPLE_SCRIPTS_DIR / out_2d

        def on_done():
            if out_2d_full.exists():
                self.display_map_image(str(out_2d_full))

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, EXAMPLE_SCRIPTS_DIR)
        else:
            self._run_cmd_async(cmd, EXAMPLE_SCRIPTS_DIR, on_finish_callback=on_done)

    def run_list_assets(self, terminal_mode=False):
        if not self._check_prerequisites(need_ue5=True, need_px4=False):
            return

        cmd = [str(VENV_PYTHON), "list_spawnable_assets.py", "--scene", "scene_px4_sitl.jsonc"]
        regex_val = self.asset_regex_entry.get().strip()
        if regex_val:
            cmd.extend(["--asset-regex", regex_val])

        if terminal_mode:
            self._run_cmd_in_terminal(cmd, EXAMPLE_SCRIPTS_DIR)
            return

        self.asset_text.delete(1.0, tk.END)

        def runner():
            try:
                env = os.environ.copy()
                env["PATH"] = f"{VENV_PYTHON.parent}:{env.get('PATH', '')}"
                res = subprocess.run(cmd, cwd=EXAMPLE_SCRIPTS_DIR, env=env, capture_output=True, text=True)
                output = res.stdout if res.stdout else res.stderr
                self.after(0, lambda: self.asset_text.insert(tk.END, output))
            except Exception as e:
                self.after(0, lambda: self.asset_text.insert(tk.END, f"Query failed: {e}"))

        threading.Thread(target=runner, daemon=True).start()


if __name__ == "__main__":
    app = DroneControlGUI()
    app.mainloop()
