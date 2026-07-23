#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DroneDigitalTwin & PX4 SITL GUI Control Panel (Bilingual: EN / ZH)
Created to automate starting Unreal Engine, PX4 SITL Docker, and Nura's Python client tools.
Uses gui_config.py for centralized configuration and dynamic path resolution.
"""

import os
import sys
import subprocess
import threading
import queue
import time
import signal
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk

# Import path configurations from gui_config.py
from gui_config import (
    PROJECT_ROOT,
    VENV_PYTHON,
    EXAMPLE_SCRIPTS_DIR,
    HALCYON_DEMO_DIR,
    DEFAULT_VIDEO_DIR,
    FLY_KEYBOARD_SH,
    UNREAL_EDITOR_PATH,
    PX4_AUTOPILOT_DIR,
    MAP_PROJECTS_DATA,
)


# =====================================================================
# Internationalization (i18n) Translations Dictionary
# =====================================================================
TEXTS = {
    "en": {
        "title": "DroneDigitalTwin + PX4 SITL Control Panel",
        "tab_control": " 🕹️ Control Panel ",
        "tab_logs": " 📜 Console & Logs ",
        "sys_controls_title": " System & Simulation Environment Controls ",
        "unreal_map": "Unreal Map: ",
        "game_mode": "-game (Auto Play on Start)",
        "btn_launch_ue": "▶ Launch Unreal Engine",
        "btn_stop_ue": "■ Stop Unreal",
        "ue_status_checking": "● UE5: Checking...",
        "ue_status_running": "● UE5: Running",
        "ue_status_starting": "● UE5: Starting...",
        "ue_status_stopped": "● UE5: Stopped",
        "px4_container": "PX4 SITL Container: ",
        "btn_launch_px4": "▶ Launch PX4 SITL Container",
        "btn_stop_px4": "■ Stop PX4 Container",
        "px4_status_checking": "● PX4: Checking...",
        "px4_status_running": "● PX4 Container: Running",
        "px4_status_starting": "● PX4 Container: Starting...",
        "px4_status_stopped": "● PX4 Container: Stopped",
        "btn_clean_restart": "🔄 Clean Restart UE5 + PX4",
        "lang_select": "🌐 Language / 語言: ",

        # Script Tabs
        "tab_keyboard": " ⌨️ Manual Flight ",
        "tab_astar": " 🧭 A* Autopilot ",
        "tab_replan": " ⚡ Dynamic Replanning ",
        "tab_fpv": " 📹 FPV Overlay ",
        "tab_cameras": " 📷 Camera & Sensors ",
        "tab_map": " 🗺️ Map Scanner ",
        "tab_assets": " 🔍 Asset Inspector ",

        # Keyboard Tab
        "kb_title": "Keyboard Manual Flight Control (keyboard_control.py / truck2ped.py)",
        "kb_script_type": "Select Script Type:",
        "kb_script_basic": "Basic Keyboard Flight (keyboard_control.py)",
        "kb_script_truck": "Truck + Pedestrian Scene (truck2ped.py)",
        "kb_use_px4": "Use PX4 SITL Scene (scene_px4_sitl.jsonc)",
        "kb_start": "Takeoff Position (--start x,y,z NED):",
        "kb_info_title": " 💡 Linux Keyboard Control Notes ",
        "kb_info_msg": (
            "On Linux, the `keyboard` package requires root permissions to capture global hotkeys.\n"
            "1. Running directly inside GUI may not respond or give Permission Denied.\n"
            "2. Recommended: Click '💻 Launch Sudo Terminal' below to control WASD in a new window.\n"
            "3. If keys still don't respond under Chrome Remote Desktop, please use 'A* Autopilot'."
        ),
        "btn_run": "▶ Execute",
        "btn_sudo_term": "💻 Launch Sudo Terminal",
        "btn_term": "💻 Terminal Execution",

        # A* Autopilot Tab
        "astar_title": "A* Path Planning & PX4 Autopilot (px4_astar_autopilot.py)",
        "preset_routes": "Quick Preset Routes: ",
        "btn_apply_preset": "Apply Preset",
        "params_title": " Flight & Planning Parameters ",
        "start_coord": "Start Position (--start):",
        "goal_coord": "Goal Position (--goal):",
        "cruise_vel": "Cruise Velocity m/s (--velocity-mps):",
        "acc_limit": "Accel Limit m/s² (--acceleration-limit-mps2):",
        "slowdown_dist": "Slowdown Dist m (--slowdown-distance-m):",
        "wp_accept": "Waypoint Acceptance m (--waypoint-acceptance-m):",
        "wp_hold": "Waypoint Hold Time sec (--waypoint-hold-sec):",
        "yaw_rate": "Turn Yaw Rate dps (--path-yaw-rate-dps):",
        "px4_timeout": "PX4 Timeout sec (--px4-ready-timeout-sec):",
        "land_at_goal": "Land at Goal (--land-at-goal)",
        "plan_only": "Plan Only (No Flight) (--plan-only debug)",
        "print_wp": "Print Waypoints (--print-waypoints)",
        "teleport_start": "Teleport to Start (--teleport-start)",
        "scene_origin": "Set Start as Scene Origin (--start-as-scene-origin)",

        # A* Presets
        "astar_preset_1": "RiverForest Map - Short Route (72,-8,-4 -> 33,-19,-6)",
        "astar_preset_2": "RiverForest Map - Long Route (72,-8,-4 -> -50,76,-25)",
        "astar_preset_3": "Blocks Map - Standard Test (30,0,-6 -> 30,-48,-10)",

        # Dynamic Replanning Tab
        "replan_title": "Dynamic Obstacle Avoidance & Path Replanning (route_replan_static.py)",
        "replan_params_title": " Avoidance & Flight Control Parameters ",
        "full_route": "Full Route Waypoints (--route N1;N2;...):",
        "flight_driver": "Flight Driver (--flight-driver):",
        "stop_dist": "Obstacle Stop Distance m (--object-stop-distance-m):",
        "emergency_node": "Emergency Detour Node (--replan-emergency-node):",
        "rejoin_point": "Rejoin Waypoint (--replan-rejoin-point):",
        "vel_lookahead": "Velocity Lookahead m (--velocity-lookahead-m):",
        "replan_on_obj": "Enable Auto Detour (--replan-on-object)",
        "third_person": "Enable 3rd-Person Chase Cam Overlay (--third-person-overlay)",

        # Replan Presets
        "replan_preset_1": "RiverForest Map - Short Route (Direct Flight No Obstacle)",
        "replan_preset_2": "RiverForest Map - Long Route (Dynamic Detour with Obstacles)",

        # FPV Overlay Tab
        "fpv_title": "FPV First Person View Path Overlay & Video Recording (fpv_route_overlay.py)",
        "fpv_info_title": " 💡 What is FPV Path Overlay & Recording? ",
        "fpv_info_msg": (
            "FPV overlay guides the drone along A* waypoints while projecting 3D path points onto front camera:\n"
            "• Visual effect: Passed/active waypoints highlight in green (like HUD / flight navigation rings).\n"
            "• Video Output: Records full flight overlay into MP4 video (default: DroneDigitalTwin/video/).\n"
            "⚠️ Prerequisite: Unreal Engine and PX4 SITL Container must be running!"
        ),
        "fpv_form_title": " Overlay & Video Settings ",
        "front_rgb_angle": "Front Camera Pitch Angle (--front-rgb-angle):",
        "wp_distance": "Waypoint Distance m (--waypoint-distance-m):",
        "min_altitude": "Min Flight Altitude m (--min-altitude):",
        "flight_speed": "Flight Speed m/s (--velocity-mps):",
        "video_output_dir": "Video Output Directory (--video-path):",
        "preview_resolution": "Preview Resolution [WxH]:",

        # Camera & Sensor Test Tab
        "cam_title": "Onboard Cameras & LiDAR Testbench (check_all_cameras.py)",
        "cam_info_title": " 💡 What is Camera & Sensor Test? ",
        "cam_info_msg": (
            "Displays OpenCV real-time preview windows showing current camera feeds:\n"
            "• RGB Cameras (Front/Left/Right/Down): Verify aerial view & visual detection.\n"
            "• Depth Camera: Colorized depth map (brighter = closer) for obstacle distance testing.\n"
            "• LiDAR: 3D point cloud & forward high-density scan (dense-forward) for radar verification.\n"
            "⚠️ Tip: Must start Unreal Engine & click Play before OpenCV windows pop up!"
        ),
        "cam_form_title": " Sensor Test Settings ",
        "test_cam_type": "Test Camera Type (--camera):",
        "lidar_preset": "LiDAR Quality Preset (--lidar-quality-preset):",
        "depth_min": "Depth Min Distance m (--depth-min-m):",
        "depth_max": "Depth Max Distance m (--depth-max-m):",
        "rgb_angle": "Front RGB Angle (--front-rgb-angle):",
        "depth_angle": "Depth Camera Angle (--depth-angle):",
        "fly_pattern": "Auto Test Flight Route (--fly-pattern)",
        "avoid_obs": "Enable Obstacle Avoidance (--avoid-obstacles)",

        # Map Viewer Tab
        "map_title": "Scene Obstacle Scan & 2D/3D Occupancy Grid Generation (px4_map_viewer.py)",
        "map_info_title": " 💡 What is Map Scanning & Occupancy Grid? ",
        "map_info_msg": (
            "Scans terrain, trees, and buildings via Unreal raycasting without flying the drone:\n"
            "• Slices at specified Z altitude (e.g. -8.0m) to generate 2D/3D occupancy maps.\n"
            "• Core Purpose: Used by A* Autopilot (`px4_astar_autopilot.py`) to compute collision-free routes.\n"
            "⚠️ Tip: Must start Unreal Engine & click Play before scanning!"
        ),
        "map_form_title": " Scanning Settings ",
        "scan_start": "Scan Start (--start):",
        "scan_goal": "Scan Goal (--goal):",
        "slice_z": "Z-Axis Slice Altitude (--slice-z-ned):",
        "grid_res": "Resolution m (--resolution-m):",
        "map_size": "Map Bounds m (--map-size):",
        "output_2d": "2D Image Output (--output):",
        "output_3d": "3D Image Output (--output-3d):",
        "btn_scan": "🗺️ Start Scan & Display PNG",
        "png_preview_title": " Occupancy Grid Preview (PNG View) ",
        "png_placeholder": "Click 'Start Scan' to generate and view 2D/3D occupancy map",

        # Asset Query Tab
        "asset_title": "Inspect Spawnable Asset IDs in Scene (list_spawnable_assets.py)",
        "asset_regex": "Asset Keyword / Regex (--asset-regex):",
        "btn_query": "🔍 Query Assets",
        "asset_res_title": " Query Results ",

        # Console & Log Tab
        "task_idle": "● Current Task: Idle",
        "task_running": "● Current Task: Running ({})",
        "btn_stop_script": "⛔ Terminate Current Python Task",
        "btn_clear_log": "🧹 Clear Log",

        # Dialog Messages
        "dialog_ue_missing_title": "Unreal Engine Not Detected",
        "dialog_ue_missing_msg": "Unreal Engine is not running!\nScripts must connect to Unreal to execute.\n\nLaunch Unreal Engine now?",
        "dialog_px4_missing_title": "PX4 SITL Container Not Detected",
        "dialog_px4_missing_msg": "This feature requires PX4 SITL (TCP 4560 connection)!\nCurrently PX4 Container is not running.\n\nLaunch PX4 Container now?",
        "dialog_restart_title": "Clean Restart",
        "dialog_restart_msg": "This will forcefully stop Unreal Engine and PX4 Container to free TCP port 4560. Proceed?",
        "dialog_busy_title": "Warning",
        "dialog_busy_msg": "A Python script is already running! Please stop the current task first.",
        "dialog_err_title": "Error",

        # Map display names
        "map_river_forest": "LowPolyRiverForest (River & Forest Map)",
        "map_blocks": "Blocks (Default AirSim Map)",
        "map_walking_npcs": "WalkingNPCs (Truck & Pedestrians)",
    },
    "zh": {
        "title": "DroneDigitalTwin + PX4 SITL 控制台",
        "tab_control": " 🕹️ 操作控制面板 ",
        "tab_logs": " 📜 執行控制台與 Log ",
        "sys_controls_title": " 系統與模擬環境控制 (System Controls) ",
        "unreal_map": "Unreal 地圖: ",
        "game_mode": "-game (開啟即 Play)",
        "btn_launch_ue": "▶ 啟動 Unreal Engine",
        "btn_stop_ue": "■ 停止 Unreal",
        "ue_status_checking": "● UE5: 檢查中",
        "ue_status_running": "● UE5: 運行中",
        "ue_status_starting": "● UE5: 啟動中...",
        "ue_status_stopped": "● UE5: 未啟動",
        "px4_container": "PX4 SITL 容器: ",
        "btn_launch_px4": "▶ 啟動 PX4 SITL Container",
        "btn_stop_px4": "■ 停止 PX4 Container",
        "px4_status_checking": "● PX4: 檢查中",
        "px4_status_running": "● PX4 Container: 運行中",
        "px4_status_starting": "● PX4 Container: 啟動中...",
        "px4_status_stopped": "● PX4 Container: 未啟動",
        "btn_clean_restart": "🔄 一鍵重啟 UE5 + PX4",
        "lang_select": "🌐 Language / 語言: ",

        # Script Tabs
        "tab_keyboard": " ⌨️ 手動飛行 ",
        "tab_astar": " 🧭 A* 自動導航 ",
        "tab_replan": " ⚡ 動態避障重規劃 ",
        "tab_fpv": " 📹 FPV 疊圖與錄影 ",
        "tab_cameras": " 📷 相機與感測器 ",
        "tab_map": " 🗺️ 地圖掃描 ",
        "tab_assets": " 🔍 資產查詢 ",

        # Keyboard Tab
        "kb_title": "鍵盤手動飛行控制 (keyboard_control.py / truck2ped.py)",
        "kb_script_type": "選擇腳本類型:",
        "kb_script_basic": "基本鍵盤飛行 (keyboard_control.py)",
        "kb_script_truck": "卡車+行人互動場景 (truck2ped.py)",
        "kb_use_px4": "使用 PX4 SITL 場景 (scene_px4_sitl.jsonc)",
        "kb_start": "起飛座標 (--start x,y,z NED):",
        "kb_info_title": " 💡 Linux 鍵盤控制須知 ",
        "kb_info_msg": (
            "在 Linux 上，`keyboard` 套件需要 root 權限才能讀取全域按鍵。\n"
            "1. 若直接執行可能無反應或提示 Permission Denied。\n"
            "2. 建議點擊下方『💻 Sudo Terminal 執行』按鈕，在新視窗操作 WASD 控制無人機。\n"
            "3. 在遠端桌面 (Chrome Remote Desktop) 環境下按鍵若仍無回應，建議切換到『A* 自動導航』頁籤。"
        ),
        "btn_run": "▶ 執行",
        "btn_sudo_term": "💻 Sudo Terminal 執行",
        "btn_term": "💻 Terminal 執行",

        # A* Autopilot Tab
        "astar_title": "A* 路徑規劃與 PX4 自動導航 (px4_astar_autopilot.py)",
        "preset_routes": "快捷預設路線: ",
        "btn_apply_preset": "套用預設",
        "params_title": " 飛行與規劃參數 ",
        "start_coord": "起點座標 (--start):",
        "goal_coord": "終點座標 (--goal):",
        "cruise_vel": "巡航速度 m/s (--velocity-mps):",
        "acc_limit": "加速度上限 m/s² (--acceleration-limit-mps2):",
        "slowdown_dist": "終點減速距離 m (--slowdown-distance-m):",
        "wp_accept": "Waypoint判定距離 m (--waypoint-acceptance-m):",
        "wp_hold": "Waypoint停留秒數 (--waypoint-hold-sec):",
        "yaw_rate": "轉彎角速度 dps (--path-yaw-rate-dps):",
        "px4_timeout": "PX4 等待逾時秒數 (--px4-ready-timeout-sec):",
        "land_at_goal": "到達終點降落 (--land-at-goal)",
        "plan_only": "只算路徑不飛行 (--plan-only 除錯用)",
        "print_wp": "印出Waypoints (--print-waypoints)",
        "teleport_start": "開場直接傳送 (--teleport-start)",
        "scene_origin": "設定為場景原點 (--start-as-scene-origin)",

        # A* Presets
        "astar_preset_1": "RiverForest 地圖 - 短程 (72,-8,-4 -> 33,-19,-6)",
        "astar_preset_2": "RiverForest 地圖 - 長程 (72,-8,-4 -> -50,76,-25)",
        "astar_preset_3": "Blocks 地圖 - 標準測試 (30,0,-6 -> 30,-48,-10)",

        # Dynamic Replanning Tab
        "replan_title": "飛行中自動動態避障與路徑重規劃 (route_replan_static.py)",
        "replan_params_title": " 避障與飛行控制參數 ",
        "full_route": "全航線點位 (--route N1;N2;...):",
        "flight_driver": "飛行控制器 (--flight-driver):",
        "stop_dist": "障礙物停等距離 m (--object-stop-distance-m):",
        "emergency_node": "繞道緊急節點 (--replan-emergency-node):",
        "rejoin_point": "繞道接回點位 (--replan-rejoin-point):",
        "vel_lookahead": "速度 Lookahead m (--velocity-lookahead-m):",
        "replan_on_obj": "開啟障礙物自動繞道 (--replan-on-object)",
        "third_person": "開啟第三人稱視角畫面疊圖 (--third-person-overlay)",

        # Replan Presets
        "replan_preset_1": "RiverForest 地圖 - 短程路線 (無障礙直飛驗證)",
        "replan_preset_2": "RiverForest 地圖 - 長程動態避障繞道 (含障礙物與緊急節點)",

        # FPV Overlay Tab
        "fpv_title": "FPV 第一人稱視角路徑點動態疊圖與錄影 (fpv_route_overlay.py)",
        "fpv_info_title": " 💡 什麼是 FPV 路徑疊圖與錄影？ ",
        "fpv_info_msg": (
            "FPV (First Person View 第一人稱視角) 會指揮無人機根據 A* 航線飛行，並將規劃好的 3D Waypoint 路徑點即時繪製在無人機前視鏡頭畫面上：\n"
            "• 畫面效果：到達的航線點會亮起綠色標記（類似戰鬥機抬頭顯示器 HUD / 飛行遊戲導航圈）。\n"
            "• 輸出功能：同時可將完整飛行與疊圖過程錄製並儲存成 MP4 影片（預設存於 DroneDigitalTwin/video/）。\n"
            "⚠️ 前置條件：必須先啟動 Unreal Engine 並啟動 PX4 SITL Container！"
        ),
        "fpv_form_title": " 畫面疊圖與錄影設定 ",
        "front_rgb_angle": "前相機俯仰角 (--front-rgb-angle):",
        "wp_distance": "Waypoint間距 m (--waypoint-distance-m):",
        "min_altitude": "最低飛行高度 m (--min-altitude):",
        "flight_speed": "飛行速度 m/s (--velocity-mps):",
        "video_output_dir": "影片輸出目錄 (--video-path):",
        "preview_resolution": "預覽解析度 [寬x高]:",

        # Camera & Sensor Test Tab
        "cam_title": "機載相機與 LiDAR 測試台 (check_all_cameras.py)",
        "cam_info_title": " 💡 什麼是相機與感測器測試？ ",
        "cam_info_msg": (
            "此工具會在電腦桌面上跳出 OpenCV 即時預覽視窗，呈現無人機當前的鏡頭畫面：\n"
            "• RGB 相機 (前後左右下): 驗證空拍畫面與視覺偵測。\n"
            "• Depth 深度相機: 顯示色彩深度圖 (越近越亮)，用於測試障礙物距離與深度感測能力。\n"
            "• LiDAR: 顯示 3D 點雲與前方高密度掃描 (dense-forward)，驗證雷達點雲覆蓋與迴避。\n"
            "⚠️ 提示：必須先啟動 Unreal Engine 並點擊 Play，腳本連上模擬器後才會彈出 OpenCV 視窗！"
        ),
        "cam_form_title": " 感測器測試設定 ",
        "test_cam_type": "測試相機種類 (--camera):",
        "lidar_preset": "LiDAR 畫質預設 (--lidar-quality-preset):",
        "depth_min": "Depth 最短距離 m (--depth-min-m):",
        "depth_max": "Depth 最長距離 m (--depth-max-m):",
        "rgb_angle": "前鏡頭角度 (--front-rgb-angle):",
        "depth_angle": "Depth 鏡頭角度 (--depth-angle):",
        "fly_pattern": "自動飛行測試航線 (--fly-pattern)",
        "avoid_obs": "開啟避障 (--avoid-obstacles)",

        # Map Viewer Tab
        "map_title": "場景障礙物掃描與 2D/3D 佔據網格圖生成 (px4_map_viewer.py)",
        "map_info_title": " 💡 什麼是地圖掃描與網格圖？ ",
        "map_info_msg": (
            "此工具不用實際飛行無人機，而是透過 Unreal 的 Raycasting 射線掃描地形、樹木與建築物。\n"
            "• 在指定 Z 軸高度切片 (例如 -8.0m)，產生黑白二值化的 2D/3D 障礙物佔據圖 (Occupancy Grid Map)。\n"
            "• 核心作用：A* 自動導航工具 (`px4_astar_autopilot.py`) 就是讀取此圖算出一條避開障礙物的可行航線。\n"
            "⚠️ 提示：必須先啟動 Unreal Engine 並點擊 Play，腳本才能連上場景進行射線掃描！"
        ),
        "map_form_title": " 掃描設定 ",
        "scan_start": "掃描起點 (--start):",
        "scan_goal": "掃描終點 (--goal):",
        "slice_z": "Z 軸高度切片 (--slice-z-ned):",
        "grid_res": "解析度 m (--resolution-m):",
        "map_size": "圖形大小 m (--map-size):",
        "output_2d": "2D 圖檔名稱 (--output):",
        "output_3d": "3D 圖檔名稱 (--output-3d):",
        "btn_scan": "🗺️ 開始掃描並顯示圖形",
        "png_preview_title": " 掃描結果圖片預覽 (PNG View) ",
        "png_placeholder": "點擊『開始掃描』後將在此顯示 2D/3D 障礙物佔據圖",

        # Asset Query Tab
        "asset_title": "查詢場景內可生成 (spawnable) 物件資產 ID (list_spawnable_assets.py)",
        "asset_regex": "資產關鍵字 / 正則表達式 (--asset-regex):",
        "btn_query": "🔍 查詢",
        "asset_res_title": " 查詢結果列表 ",

        # Console & Log Tab
        "task_idle": "● 當前任務: 空閒 (Idle)",
        "task_running": "● 當前任務: 執行中 ({})",
        "btn_stop_script": "⛔ 終止當前 Python 任務",
        "btn_clear_log": "🧹 清空 Log",

        # Dialog Messages
        "dialog_ue_missing_title": "未偵測到 Unreal Engine",
        "dialog_ue_missing_msg": "Unreal Engine 尚未啟動！\n腳本必須連上 Unreal 才能執行。\n\n是否立即啟動 Unreal Engine？",
        "dialog_px4_missing_title": "未偵測到 PX4 SITL 容器",
        "dialog_px4_missing_msg": "此功能需要 PX4 飛控 (TCP 4560 連線)！\n當前 PX4 Container 尚未啟動。\n\n是否協助啟動 PX4 Container？",
        "dialog_restart_title": "一鍵重啟",
        "dialog_restart_msg": "這將強制關閉 Unreal Engine 與 PX4 容器以釋放 TCP 4560 連線，確定執行嗎？",
        "dialog_busy_title": "警告",
        "dialog_busy_msg": "已有 Python 腳本正在執行中！請先終止當前腳本。",
        "dialog_err_title": "錯誤",

        # Map display names
        "map_river_forest": "LowPolyRiverForest (河流與森林地圖)",
        "map_blocks": "Blocks (原生測試地圖)",
        "map_walking_npcs": "WalkingNPCs (卡車與行人)",
    }
}


class DroneControlGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # Default language: English ("en")
        self.current_lang = "en"

        self.geometry("1080x820")
        self.minsize(900, 680)

        # Style configuration
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure("TNotebook.Tab", font=("TkDefaultFont", 10, "bold"), padding=[10, 5])

        # Process management handles
        self.ue5_process = None
        self.active_script_process = None

        # State indicators
        self.is_ue5_running = False
        self.is_px4_running = False

        # Thread queue for UI log updates
        self.log_queue = queue.Queue()

        self._create_widgets()
        self.update_ui_language()
        self._start_status_checker()
        self._process_log_queue()

    def t(self, key):
        """Helper to fetch translated text according to current_lang."""
        return TEXTS.get(self.current_lang, TEXTS["en"]).get(key, key)

    def _create_widgets(self):
        # Master Notebook dividing Control Panel & Console Log
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Control Panel
        self.panel_tab = ttk.Frame(self.main_notebook, padding=10)
        self.main_notebook.add(self.panel_tab, text="")

        # Tab 2: Console Log
        self.log_tab = ttk.Frame(self.main_notebook, padding=10)
        self.main_notebook.add(self.log_tab, text="")

        # -------------------------------------------------------------
        # Language Switcher placed on top-right blank area of main_notebook tabs
        # -------------------------------------------------------------
        self.lang_frame = ttk.Frame(self)
        self.lang_label = ttk.Label(self.lang_frame, text="", font=("TkDefaultFont", 9, "bold"))
        self.lang_label.pack(side=tk.LEFT, padx=(0, 4))

        self.lang_var = tk.StringVar(value="English")
        self.lang_combo = ttk.Combobox(self.lang_frame, textvariable=self.lang_var, values=["English", "繁體中文"], state="readonly", width=10)
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        self.lang_frame.place(relx=1.0, x=-12, y=8, anchor="ne")
        self.lang_frame.lift()

        # -------------------------------------------------------------
        # Control Panel Widgets
        # -------------------------------------------------------------
        self.top_frame = ttk.LabelFrame(self.panel_tab, text="", padding=10)
        self.top_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        # Unreal Engine Controls
        ue_frame = ttk.Frame(self.top_frame)
        ue_frame.pack(fill=tk.X, pady=2)

        self.map_lbl = ttk.Label(ue_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.map_lbl.pack(side=tk.LEFT, padx=(0, 5))

        self.map_var = tk.StringVar()
        self.map_combo = ttk.Combobox(ue_frame, textvariable=self.map_var, state="readonly", width=36)
        self.map_combo.pack(side=tk.LEFT, padx=(0, 10))

        self.game_mode_var = tk.BooleanVar(value=True)
        self.game_mode_chk = ttk.Checkbutton(ue_frame, text="", variable=self.game_mode_var)
        self.game_mode_chk.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_launch_ue = ttk.Button(ue_frame, text="", command=self.launch_unreal)
        self.btn_launch_ue.pack(side=tk.LEFT, padx=3)

        self.btn_stop_ue = ttk.Button(ue_frame, text="", command=self.stop_unreal)
        self.btn_stop_ue.pack(side=tk.LEFT, padx=3)

        self.ue_status_label = ttk.Label(ue_frame, text="", foreground="gray", font=("TkDefaultFont", 10, "bold"))
        self.ue_status_label.pack(side=tk.LEFT, padx=(15, 0))

        # PX4 Container Controls
        px4_frame = ttk.Frame(self.top_frame)
        px4_frame.pack(fill=tk.X, pady=(8, 2))

        self.px4_lbl = ttk.Label(px4_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.px4_lbl.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_launch_px4 = ttk.Button(px4_frame, text="", command=self.launch_px4)
        self.btn_launch_px4.pack(side=tk.LEFT, padx=3)

        self.btn_stop_px4 = ttk.Button(px4_frame, text="", command=self.stop_px4)
        self.btn_stop_px4.pack(side=tk.LEFT, padx=3)

        self.px4_status_label = ttk.Label(px4_frame, text="", foreground="gray", font=("TkDefaultFont", 10, "bold"))
        self.px4_status_label.pack(side=tk.LEFT, padx=(15, 20))

        # Clean restart
        self.btn_clean_restart = ttk.Button(px4_frame, text="", command=self.clean_restart_environment)
        self.btn_clean_restart.pack(side=tk.RIGHT, padx=5)

        # Sub-Notebook for Script Tools
        self.script_notebook = ttk.Notebook(self.panel_tab)
        self.script_notebook.pack(fill=tk.BOTH, expand=True)

        self._setup_tab_keyboard()
        self._setup_tab_astar()
        self._setup_tab_replan()
        self._setup_tab_fpv()
        self._setup_tab_cameras()
        self._setup_tab_map_viewer()
        self._setup_tab_assets()

        # -------------------------------------------------------------
        # Console Log Widgets
        # -------------------------------------------------------------
        log_bar = ttk.Frame(self.log_tab)
        log_bar.pack(fill=tk.X, pady=(0, 8))

        self.script_status_label = ttk.Label(log_bar, text="", font=("TkDefaultFont", 11, "bold"), foreground="green")
        self.script_status_label.pack(side=tk.LEFT, padx=5)

        self.btn_stop_script = ttk.Button(log_bar, text="", command=self.stop_active_script, state=tk.DISABLED)
        self.btn_stop_script.pack(side=tk.RIGHT, padx=5)

        self.btn_clear_log = ttk.Button(log_bar, text="", command=self.clear_log)
        self.btn_clear_log.pack(side=tk.RIGHT, padx=5)

        # Log Text Box
        self.log_text = tk.Text(self.log_tab, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", font=("Monospace", 10))
        self.log_scrollbar = ttk.Scrollbar(self.log_tab, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _on_language_change(self, event=None):
        val = self.lang_var.get()
        if "中文" in val:
            self.current_lang = "zh"
        else:
            self.current_lang = "en"
        self.update_ui_language()

    def update_ui_language(self):
        """Update all text across the entire UI dynamically."""
        self.title(self.t("title"))
        self.main_notebook.tab(0, text=self.t("tab_control"))
        self.main_notebook.tab(1, text=self.t("tab_logs"))

        self.top_frame.config(text=self.t("sys_controls_title"))
        self.lang_label.config(text=self.t("lang_select"))
        self.map_lbl.config(text=self.t("unreal_map"))
        self.game_mode_chk.config(text=self.t("game_mode"))
        self.btn_launch_ue.config(text=self.t("btn_launch_ue"))
        self.btn_stop_ue.config(text=self.t("btn_stop_ue"))
        self.px4_lbl.config(text=self.t("px4_container"))
        self.btn_launch_px4.config(text=self.t("btn_launch_px4"))
        self.btn_stop_px4.config(text=self.t("btn_stop_px4"))
        self.btn_clean_restart.config(text=self.t("btn_clean_restart"))

        if hasattr(self, 'lang_frame'):
            self.lang_frame.lift()

        # Map Combobox values update
        map_options = [self.t(key) for key, _ in MAP_PROJECTS_DATA]
        curr_idx = max(0, self.map_combo.current()) if self.map_combo['values'] else 0
        self.map_combo['values'] = map_options
        self.map_combo.current(min(curr_idx, len(map_options) - 1))

        # Script Notebook Tab titles
        self.script_notebook.tab(0, text=self.t("tab_keyboard"))
        self.script_notebook.tab(1, text=self.t("tab_astar"))
        self.script_notebook.tab(2, text=self.t("tab_replan"))
        self.script_notebook.tab(3, text=self.t("tab_fpv"))
        self.script_notebook.tab(4, text=self.t("tab_cameras"))
        self.script_notebook.tab(5, text=self.t("tab_map"))
        self.script_notebook.tab(6, text=self.t("tab_assets"))

        # Tab 1: Keyboard
        self.kb_title_lbl.config(text=self.t("kb_title"))
        self.kb_type_lbl.config(text=self.t("kb_script_type"))
        self.kb_rb_basic.config(text=self.t("kb_script_basic"))
        self.kb_rb_truck.config(text=self.t("kb_script_truck"))
        self.kb_chk_px4.config(text=self.t("kb_use_px4"))
        self.kb_start_lbl.config(text=self.t("kb_start"))
        self.kb_info_box.config(text=self.t("kb_info_title"))
        self.kb_info_lbl.config(text=self.t("kb_info_msg"))
        self.kb_btn_run.config(text=self.t("btn_run"))
        self.kb_btn_sudo.config(text=self.t("btn_sudo_term"))

        # Tab 2: A* Autopilot
        self.astar_title_lbl.config(text=self.t("astar_title"))
        self.astar_preset_lbl.config(text=self.t("preset_routes"))
        self.astar_btn_preset.config(text=self.t("btn_apply_preset"))
        self.astar_form_frame.config(text=self.t("params_title"))
        self.astar_land_chk.config(text=self.t("land_at_goal"))
        self.astar_plan_chk.config(text=self.t("plan_only"))
        self.astar_print_chk.config(text=self.t("print_wp"))
        self.astar_teleport_chk.config(text=self.t("teleport_start"))
        self.astar_origin_chk.config(text=self.t("scene_origin"))
        self.astar_btn_run.config(text=self.t("btn_run"))
        self.astar_btn_term.config(text=self.t("btn_term"))
        self.astar_label_refs["start"].config(text=self.t("start_coord"))
        self.astar_label_refs["goal"].config(text=self.t("goal_coord"))
        self.astar_label_refs["vel"].config(text=self.t("cruise_vel"))
        self.astar_label_refs["acc"].config(text=self.t("acc_limit"))
        self.astar_label_refs["slowdown"].config(text=self.t("slowdown_dist"))
        self.astar_label_refs["accept"].config(text=self.t("wp_accept"))
        self.astar_label_refs["hold"].config(text=self.t("wp_hold"))
        self.astar_label_refs["yaw_rate"].config(text=self.t("yaw_rate"))
        self.astar_label_refs["timeout"].config(text=self.t("px4_timeout"))

        ast_idx = max(0, self.astar_preset_combo.current())
        self.astar_preset_combo['values'] = [
            self.t("astar_preset_1"),
            self.t("astar_preset_2"),
            self.t("astar_preset_3"),
        ]
        self.astar_preset_combo.current(min(ast_idx, 2))

        # Tab 3: Dynamic Replanning
        self.replan_title_lbl.config(text=self.t("replan_title"))
        self.replan_preset_lbl.config(text=self.t("preset_routes"))
        self.replan_btn_preset.config(text=self.t("btn_apply_preset"))
        self.replan_form_frame.config(text=self.t("replan_params_title"))
        self.replan_route_lbl.config(text=self.t("full_route"))
        self.replan_obj_chk.config(text=self.t("replan_on_obj"))
        self.replan_overlay_chk.config(text=self.t("third_person"))
        self.replan_origin_chk.config(text=self.t("scene_origin"))
        self.replan_btn_run.config(text=self.t("btn_run"))
        self.replan_btn_term.config(text=self.t("btn_term"))
        self.replan_label_refs["start"].config(text=self.t("start_coord"))
        self.replan_label_refs["driver"].config(text=self.t("flight_driver"))
        self.replan_label_refs["stop_dist"].config(text=self.t("stop_dist"))
        self.replan_label_refs["emergency"].config(text=self.t("emergency_node"))
        self.replan_label_refs["rejoin"].config(text=self.t("rejoin_point"))
        self.replan_label_refs["lookahead"].config(text=self.t("vel_lookahead"))
        self.replan_label_refs["yaw_rate"].config(text=self.t("yaw_rate"))
        self.replan_label_refs["acc"].config(text=self.t("acc_limit"))

        rep_idx = max(0, self.replan_preset_combo.current())
        self.replan_preset_combo['values'] = [
            self.t("replan_preset_1"),
            self.t("replan_preset_2"),
        ]
        self.replan_preset_combo.current(min(rep_idx, 1))

        # Tab 4: FPV Overlay
        self.fpv_title_lbl.config(text=self.t("fpv_title"))
        self.fpv_info_box.config(text=self.t("fpv_info_title"))
        self.fpv_info_lbl.config(text=self.t("fpv_info_msg"))
        self.fpv_form_frame.config(text=self.t("fpv_form_title"))
        self.fpv_origin_chk.config(text=self.t("scene_origin"))
        self.fpv_btn_run.config(text=self.t("btn_run"))
        self.fpv_btn_term.config(text=self.t("btn_term"))
        self.fpv_label_refs["start"].config(text=self.t("start_coord"))
        self.fpv_label_refs["goal"].config(text=self.t("goal_coord"))
        self.fpv_label_refs["angle"].config(text=self.t("front_rgb_angle"))
        self.fpv_label_refs["wp_dist"].config(text=self.t("wp_distance"))
        self.fpv_label_refs["min_alt"].config(text=self.t("min_altitude"))
        self.fpv_label_refs["vel"].config(text=self.t("flight_speed"))
        self.fpv_label_refs["v_path"].config(text=self.t("video_output_dir"))
        self.fpv_label_refs["res"].config(text=self.t("preview_resolution"))

        # Tab 5: Camera & Sensors
        self.cam_title_lbl.config(text=self.t("cam_title"))
        self.cam_info_box.config(text=self.t("cam_info_title"))
        self.cam_info_lbl.config(text=self.t("cam_info_msg"))
        self.cam_form_frame.config(text=self.t("cam_form_title"))
        self.cam_type_lbl.config(text=self.t("test_cam_type"))
        self.cam_lidar_lbl.config(text=self.t("lidar_preset"))
        self.cam_fly_chk.config(text=self.t("fly_pattern"))
        self.cam_avoid_chk.config(text=self.t("avoid_obs"))
        self.cam_teleport_chk.config(text=self.t("teleport_start"))
        self.cam_btn_run.config(text=self.t("btn_run"))
        self.cam_btn_term.config(text=self.t("btn_term"))
        self.cam_label_refs["d_min"].config(text=self.t("depth_min"))
        self.cam_label_refs["d_max"].config(text=self.t("depth_max"))
        self.cam_label_refs["rgb_ang"].config(text=self.t("rgb_angle"))
        self.cam_label_refs["dep_ang"].config(text=self.t("depth_angle"))
        self.cam_label_refs["start"].config(text=self.t("start_coord"))

        # Tab 6: Map Scanner
        self.map_title_lbl.config(text=self.t("map_title"))
        self.map_info_box.config(text=self.t("map_info_title"))
        self.map_info_lbl.config(text=self.t("map_info_msg"))
        self.map_form_frame.config(text=self.t("map_form_title"))
        self.map_btn_scan.config(text=self.t("btn_scan"))
        self.map_btn_term.config(text=self.t("btn_term"))
        self.map_img_frame.config(text=self.t("png_preview_title"))
        if not hasattr(self.img_label, 'image') or self.img_label.image is None:
            self.img_label.config(text=self.t("png_placeholder"))
        self.map_label_refs["start"].config(text=self.t("scan_start"))
        self.map_label_refs["goal"].config(text=self.t("scan_goal"))
        self.map_label_refs["slice_z"].config(text=self.t("slice_z"))
        self.map_label_refs["res"].config(text=self.t("grid_res"))
        self.map_label_refs["size"].config(text=self.t("map_size"))
        self.map_label_refs["out_2d"].config(text=self.t("output_2d"))
        self.map_label_refs["out_3d"].config(text=self.t("output_3d"))

        # Tab 7: Assets Query
        self.asset_title_lbl.config(text=self.t("asset_title"))
        self.asset_regex_lbl.config(text=self.t("asset_regex"))
        self.asset_btn_query.config(text=self.t("btn_query"))
        self.asset_btn_term.config(text=self.t("btn_term"))
        self.asset_res_frame.config(text=self.t("asset_res_title"))

        # Console Log tab
        self.btn_stop_script.config(text=self.t("btn_stop_script"))
        self.btn_clear_log.config(text=self.t("btn_clear_log"))
        if not self.active_script_process:
            self.script_status_label.config(text=self.t("task_idle"), foreground="green")

        # Update status labels
        self._update_status_ui(self.is_ue5_running, self.is_px4_running)

    # -----------------------------------------------------------------
    # Helper: Check prerequisites before script runs
    # -----------------------------------------------------------------
    def _check_prerequisites(self, need_ue5=True, need_px4=False):
        if need_ue5 and not self.is_ue5_running:
            if messagebox.askyesno(self.t("dialog_ue_missing_title"), self.t("dialog_ue_missing_msg")):
                self.launch_unreal()
                time.sleep(2)
            else:
                return False

        if need_px4 and not self.is_px4_running:
            if messagebox.askyesno(self.t("dialog_px4_missing_title"), self.t("dialog_px4_missing_msg")):
                self.launch_px4()
                time.sleep(2)
            else:
                return False

        return True

    # -----------------------------------------------------------------
    # Helper: Open interactive Terminal window with dynamic user/host prompt
    # -----------------------------------------------------------------
    def _run_cmd_in_terminal(self, cmd_args, cwd):
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
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.kb_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.kb_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_mode = ttk.Frame(tab)
        f_mode.pack(fill=tk.X, pady=5)
        self.kb_type_lbl = ttk.Label(f_mode, text="")
        self.kb_type_lbl.pack(side=tk.LEFT, padx=(0, 10))
        self.kb_script_var = tk.StringVar(value="keyboard_control.py")
        self.kb_rb_basic = ttk.Radiobutton(f_mode, text="", variable=self.kb_script_var, value="keyboard_control.py")
        self.kb_rb_basic.pack(side=tk.LEFT, padx=10)
        self.kb_rb_truck = ttk.Radiobutton(f_mode, text="", variable=self.kb_script_var, value="truck2ped.py")
        self.kb_rb_truck.pack(side=tk.LEFT, padx=10)

        f_px4 = ttk.Frame(tab)
        f_px4.pack(fill=tk.X, pady=5)
        self.kb_use_px4_var = tk.BooleanVar(value=True)
        self.kb_chk_px4 = ttk.Checkbutton(f_px4, text="", variable=self.kb_use_px4_var)
        self.kb_chk_px4.pack(side=tk.LEFT)

        f_start = ttk.Frame(tab)
        f_start.pack(fill=tk.X, pady=5)
        self.kb_start_lbl = ttk.Label(f_start, text="")
        self.kb_start_lbl.pack(side=tk.LEFT, padx=(0, 10))
        self.kb_start_entry = ttk.Entry(f_start, width=20)
        self.kb_start_entry.insert(0, "30,0,-6")
        self.kb_start_entry.pack(side=tk.LEFT)

        self.kb_info_box = ttk.LabelFrame(tab, text="", padding=10)
        self.kb_info_box.pack(fill=tk.X, pady=15)
        self.kb_info_lbl = ttk.Label(self.kb_info_box, text="", foreground="#333333", justify=tk.LEFT)
        self.kb_info_lbl.pack(anchor=tk.W)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=10)
        self.kb_btn_run = ttk.Button(btn_frame, text="", command=self.run_keyboard_control)
        self.kb_btn_run.pack(side=tk.LEFT, padx=5)
        self.kb_btn_sudo = ttk.Button(btn_frame, text="", command=self.run_keyboard_control_sudo)
        self.kb_btn_sudo.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 2: A* Autopilot
    # -----------------------------------------------------------------
    def _setup_tab_astar(self):
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.astar_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.astar_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_preset = ttk.Frame(tab)
        f_preset.pack(fill=tk.X, pady=5)
        self.astar_preset_lbl = ttk.Label(f_preset, text="")
        self.astar_preset_lbl.pack(side=tk.LEFT, padx=(0, 5))

        self.astar_preset_combo = ttk.Combobox(f_preset, state="readonly", width=50)
        self.astar_preset_combo.pack(side=tk.LEFT, padx=5)
        self.astar_btn_preset = ttk.Button(f_preset, text="", command=self.apply_astar_preset)
        self.astar_btn_preset.pack(side=tk.LEFT, padx=5)

        self.astar_form_frame = ttk.LabelFrame(tab, text="", padding=10)
        self.astar_form_frame.pack(fill=tk.X, pady=10)
        self.astar_form_frame.columnconfigure(1, weight=1)
        self.astar_form_frame.columnconfigure(3, weight=1)

        self.astar_entries = {}
        self.astar_label_refs = {}
        fields = [
            ("start_coord", "72,-8,-4", 0, 0, "start"),
            ("goal_coord", "33,-19,-6", 0, 2, "goal"),
            ("cruise_vel", "2.0", 1, 0, "vel"),
            ("acc_limit", "1.5", 1, 2, "acc"),
            ("slowdown_dist", "6.0", 2, 0, "slowdown"),
            ("wp_accept", "1.5", 2, 2, "accept"),
            ("wp_hold", "3.0", 3, 0, "hold"),
            ("yaw_rate", "10.0", 3, 2, "yaw_rate"),
            ("px4_timeout", "300", 4, 0, "timeout"),
        ]

        for key_text, default_val, row, col, key in fields:
            lbl = ttk.Label(self.astar_form_frame, text="")
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.astar_label_refs[key] = lbl

            entry = ttk.Entry(self.astar_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.astar_entries[key] = entry

        chk_frame = ttk.Frame(self.astar_form_frame)
        chk_frame.grid(row=5, column=0, columnspan=4, sticky=tk.W, pady=8)

        self.astar_land_var = tk.BooleanVar(value=True)
        self.astar_land_chk = ttk.Checkbutton(chk_frame, text="", variable=self.astar_land_var)
        self.astar_land_chk.pack(side=tk.LEFT, padx=8)

        self.astar_plan_only_var = tk.BooleanVar(value=False)
        self.astar_plan_chk = ttk.Checkbutton(chk_frame, text="", variable=self.astar_plan_only_var)
        self.astar_plan_chk.pack(side=tk.LEFT, padx=8)

        self.astar_print_wp_var = tk.BooleanVar(value=True)
        self.astar_print_chk = ttk.Checkbutton(chk_frame, text="", variable=self.astar_print_wp_var)
        self.astar_print_chk.pack(side=tk.LEFT, padx=8)

        self.astar_teleport_var = tk.BooleanVar(value=False)
        self.astar_teleport_chk = ttk.Checkbutton(chk_frame, text="", variable=self.astar_teleport_var)
        self.astar_teleport_chk.pack(side=tk.LEFT, padx=8)

        self.astar_scene_origin_var = tk.BooleanVar(value=True)
        self.astar_origin_chk = ttk.Checkbutton(chk_frame, text="", variable=self.astar_scene_origin_var)
        self.astar_origin_chk.pack(side=tk.LEFT, padx=8)

        btn_f = ttk.Frame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.astar_btn_run = ttk.Button(btn_f, text="", command=self.run_astar_autopilot)
        self.astar_btn_run.pack(side=tk.LEFT, padx=5)
        self.astar_btn_term = ttk.Button(btn_f, text="", command=lambda: self.run_astar_autopilot(terminal_mode=True))
        self.astar_btn_term.pack(side=tk.LEFT, padx=5)

    def apply_astar_preset(self):
        idx = self.astar_preset_combo.current()
        if idx == 0:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "72,-8,-4")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "33,-19,-6")
            self.astar_scene_origin_var.set(True)
        elif idx == 1:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "72,-8,-4")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "-50,76,-25")
            self.astar_scene_origin_var.set(True)
        elif idx == 2:
            self.astar_entries["start"].delete(0, tk.END); self.astar_entries["start"].insert(0, "30,0,-6")
            self.astar_entries["goal"].delete(0, tk.END); self.astar_entries["goal"].insert(0, "30,-48,-10")
            self.astar_scene_origin_var.set(False)

    # -----------------------------------------------------------------
    # Tab 3: Dynamic Re-planning
    # -----------------------------------------------------------------
    def _setup_tab_replan(self):
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.replan_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.replan_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_preset = ttk.Frame(tab)
        f_preset.pack(fill=tk.X, pady=5)
        self.replan_preset_lbl = ttk.Label(f_preset, text="")
        self.replan_preset_lbl.pack(side=tk.LEFT, padx=(0, 5))

        self.replan_preset_combo = ttk.Combobox(f_preset, state="readonly", width=55)
        self.replan_preset_combo.pack(side=tk.LEFT, padx=5)
        self.replan_btn_preset = ttk.Button(f_preset, text="", command=self.apply_replan_preset)
        self.replan_btn_preset.pack(side=tk.LEFT, padx=5)

        self.replan_form_frame = ttk.LabelFrame(tab, text="", padding=10)
        self.replan_form_frame.pack(fill=tk.X, pady=10)

        self.replan_route_lbl = ttk.Label(self.replan_form_frame, text="")
        self.replan_route_lbl.grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.replan_route_entry = ttk.Entry(self.replan_form_frame, width=80)
        self.replan_route_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=4)

        self.replan_form_frame.columnconfigure(1, weight=1)
        self.replan_form_frame.columnconfigure(3, weight=1)

        self.replan_entries = {}
        self.replan_label_refs = {}
        fields = [
            ("start_coord", "72,-8.0,-4.0", 1, 0, "start"),
            ("flight_driver", "velocity", 1, 2, "driver"),
            ("stop_dist", "2.0", 2, 0, "stop_dist"),
            ("emergency_node", "62.18,-0.41,-5.38", 2, 2, "emergency"),
            ("rejoin_point", "45.0,17.0,-16.0", 3, 0, "rejoin"),
            ("vel_lookahead", "8.0", 3, 2, "lookahead"),
            ("yaw_rate", "10.0", 4, 0, "yaw_rate"),
            ("acc_limit", "1.0", 4, 2, "acc"),
        ]

        for key_text, default_val, row, col, key in fields:
            lbl = ttk.Label(self.replan_form_frame, text="")
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.replan_label_refs[key] = lbl

            entry = ttk.Entry(self.replan_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.replan_entries[key] = entry

        chk_frame = ttk.Frame(self.replan_form_frame)
        chk_frame.grid(row=5, column=0, columnspan=4, sticky=tk.W, pady=8)

        self.replan_on_object_var = tk.BooleanVar(value=True)
        self.replan_obj_chk = ttk.Checkbutton(chk_frame, text="", variable=self.replan_on_object_var)
        self.replan_obj_chk.pack(side=tk.LEFT, padx=8)

        self.replan_overlay_var = tk.BooleanVar(value=True)
        self.replan_overlay_chk = ttk.Checkbutton(chk_frame, text="", variable=self.replan_overlay_var)
        self.replan_overlay_chk.pack(side=tk.LEFT, padx=8)

        self.replan_origin_var = tk.BooleanVar(value=True)
        self.replan_origin_chk = ttk.Checkbutton(chk_frame, text="", variable=self.replan_origin_var)
        self.replan_origin_chk.pack(side=tk.LEFT, padx=8)

        self.apply_replan_preset()

        btn_f = ttk.Frame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.replan_btn_run = ttk.Button(btn_f, text="", command=self.run_replan_static)
        self.replan_btn_run.pack(side=tk.LEFT, padx=5)
        self.replan_btn_term = ttk.Button(btn_f, text="", command=lambda: self.run_replan_static(terminal_mode=True))
        self.replan_btn_term.pack(side=tk.LEFT, padx=5)

    def apply_replan_preset(self):
        idx = max(0, self.replan_preset_combo.current())
        if idx == 0:
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
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.fpv_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.fpv_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.fpv_info_box = ttk.LabelFrame(tab, text="", padding=10)
        self.fpv_info_box.pack(fill=tk.X, pady=(0, 10))
        self.fpv_info_lbl = ttk.Label(self.fpv_info_box, text="", justify=tk.LEFT, foreground="#333333")
        self.fpv_info_lbl.pack(anchor=tk.W)

        self.fpv_form_frame = ttk.LabelFrame(tab, text="", padding=10)
        self.fpv_form_frame.pack(fill=tk.X, pady=10)
        self.fpv_form_frame.columnconfigure(1, weight=1)
        self.fpv_form_frame.columnconfigure(3, weight=1)

        self.fpv_entries = {}
        self.fpv_label_refs = {}
        fields = [
            ("start_coord", "72,-8,-4", 0, 0, "start"),
            ("goal_coord", "-50, 76, -25", 0, 2, "goal"),
            ("front_rgb_angle", "25", 1, 0, "angle"),
            ("wp_distance", "30", 1, 2, "wp_dist"),
            ("min_altitude", "32", 2, 0, "min_alt"),
            ("flight_speed", "3.0", 2, 2, "vel"),
            ("video_output_dir", DEFAULT_VIDEO_DIR, 3, 0, "v_path"),
            ("preview_resolution", "1920x1080", 3, 2, "res"),
        ]

        for key_text, default_val, row, col, key in fields:
            lbl = ttk.Label(self.fpv_form_frame, text="")
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.fpv_label_refs[key] = lbl

            entry = ttk.Entry(self.fpv_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.fpv_entries[key] = entry

        self.fpv_scene_origin_var = tk.BooleanVar(value=True)
        self.fpv_origin_chk = ttk.Checkbutton(self.fpv_form_frame, text="", variable=self.fpv_scene_origin_var)
        self.fpv_origin_chk.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=8)

        btn_f = ttk.Frame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.fpv_btn_run = ttk.Button(btn_f, text="", command=self.run_fpv_overlay)
        self.fpv_btn_run.pack(side=tk.LEFT, padx=5)
        self.fpv_btn_term = ttk.Button(btn_f, text="", command=lambda: self.run_fpv_overlay(terminal_mode=True))
        self.fpv_btn_term.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 5: Camera & Sensor Test
    # -----------------------------------------------------------------
    def _setup_tab_cameras(self):
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.cam_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.cam_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.cam_info_box = ttk.LabelFrame(tab, text="", padding=10)
        self.cam_info_box.pack(fill=tk.X, pady=(0, 10))
        self.cam_info_lbl = ttk.Label(self.cam_info_box, text="", justify=tk.LEFT, foreground="#333333")
        self.cam_info_lbl.pack(anchor=tk.W)

        self.cam_form_frame = ttk.LabelFrame(tab, text="", padding=10)
        self.cam_form_frame.pack(fill=tk.X, pady=10)
        self.cam_form_frame.columnconfigure(1, weight=1)
        self.cam_form_frame.columnconfigure(3, weight=1)

        self.cam_type_lbl = ttk.Label(self.cam_form_frame, text="")
        self.cam_type_lbl.grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)

        self.cam_type_var = tk.StringVar(value="all")
        cam_combo = ttk.Combobox(self.cam_form_frame, textvariable=self.cam_type_var, values=["all", "rgb", "depth", "lidar"], state="readonly")
        cam_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=4)

        self.cam_lidar_lbl = ttk.Label(self.cam_form_frame, text="")
        self.cam_lidar_lbl.grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)

        self.lidar_preset_var = tk.StringVar(value="dense-forward")
        lidar_combo = ttk.Combobox(self.cam_form_frame, textvariable=self.lidar_preset_var, values=["dense-forward", "default", "sparse"], state="readonly")
        lidar_combo.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=4)

        self.cam_entries = {}
        self.cam_label_refs = {}
        fields = [
            ("depth_min", "0.1", 1, 0, "d_min"),
            ("depth_max", "80.0", 1, 2, "d_max"),
            ("rgb_angle", "25", 2, 0, "rgb_ang"),
            ("depth_angle", "25", 2, 2, "dep_ang"),
            ("start_coord", "0,0,-28", 3, 0, "start"),
        ]

        for key_text, default_val, row, col, key in fields:
            lbl = ttk.Label(self.cam_form_frame, text="")
            lbl.grid(row=row, column=col, sticky=tk.W, padx=5, pady=4)
            self.cam_label_refs[key] = lbl

            entry = ttk.Entry(self.cam_form_frame)
            entry.insert(0, default_val)
            entry.grid(row=row, column=col+1, sticky=tk.EW, padx=5, pady=4)
            self.cam_entries[key] = entry

        chk_frame = ttk.Frame(self.cam_form_frame)
        chk_frame.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=8)

        self.cam_fly_pattern_var = tk.BooleanVar(value=True)
        self.cam_fly_chk = ttk.Checkbutton(chk_frame, text="", variable=self.cam_fly_pattern_var)
        self.cam_fly_chk.pack(side=tk.LEFT, padx=8)

        self.cam_avoid_var = tk.BooleanVar(value=True)
        self.cam_avoid_chk = ttk.Checkbutton(chk_frame, text="", variable=self.cam_avoid_var)
        self.cam_avoid_chk.pack(side=tk.LEFT, padx=8)

        self.cam_teleport_var = tk.BooleanVar(value=True)
        self.cam_teleport_chk = ttk.Checkbutton(chk_frame, text="", variable=self.cam_teleport_var)
        self.cam_teleport_chk.pack(side=tk.LEFT, padx=8)

        btn_f = ttk.Frame(tab)
        btn_f.pack(anchor=tk.W, pady=10)
        self.cam_btn_run = ttk.Button(btn_f, text="", command=self.run_check_cameras)
        self.cam_btn_run.pack(side=tk.LEFT, padx=5)
        self.cam_btn_term = ttk.Button(btn_f, text="", command=lambda: self.run_check_cameras(terminal_mode=True))
        self.cam_btn_term.pack(side=tk.LEFT, padx=5)

    # -----------------------------------------------------------------
    # Tab 6: Map Viewer & Scanning
    # -----------------------------------------------------------------
    def _setup_tab_map_viewer(self):
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.map_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.map_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        self.map_info_box = ttk.LabelFrame(tab, text="", padding=10)
        self.map_info_box.pack(fill=tk.X, pady=(0, 10))
        self.map_info_lbl = ttk.Label(self.map_info_box, text="", justify=tk.LEFT, foreground="#333333")
        self.map_info_lbl.pack(anchor=tk.W)

        top_split = ttk.Frame(tab)
        top_split.pack(fill=tk.BOTH, expand=True)

        self.map_form_frame = ttk.LabelFrame(top_split, text="", padding=10)
        self.map_form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.map_entries = {}
        self.map_label_refs = {}
        fields = [
            ("scan_start", "40,-20,-6", "start"),
            ("scan_goal", "50,20,-6", "goal"),
            ("slice_z", "-8.0", "slice_z"),
            ("grid_res", "1.0", "res"),
            ("map_size", "500,500,10", "size"),
            ("output_2d", "riverside_forest.png", "out_2d"),
            ("output_3d", "riverside_forest_3d.png", "out_3d"),
        ]

        for i, (key_text, default_val, key) in enumerate(fields):
            lbl = ttk.Label(self.map_form_frame, text="")
            lbl.grid(row=i, column=0, sticky=tk.W, padx=5, pady=4)
            self.map_label_refs[key] = lbl

            entry = ttk.Entry(self.map_form_frame, width=22)
            entry.insert(0, default_val)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=4)
            self.map_entries[key] = entry

        btn_f = ttk.Frame(self.map_form_frame)
        btn_f.grid(row=len(fields), column=0, columnspan=2, pady=15)
        self.map_btn_scan = ttk.Button(btn_f, text="", command=self.run_map_viewer)
        self.map_btn_scan.pack(side=tk.TOP, fill=tk.X, pady=2)
        self.map_btn_term = ttk.Button(btn_f, text="", command=lambda: self.run_map_viewer(terminal_mode=True))
        self.map_btn_term.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.map_img_frame = ttk.LabelFrame(top_split, text="", padding=5)
        self.map_img_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.img_label = ttk.Label(self.map_img_frame, text="", anchor=tk.CENTER)
        self.img_label.pack(fill=tk.BOTH, expand=True)

    def display_map_image(self, image_path):
        try:
            if not os.path.exists(image_path):
                return
            img = Image.open(image_path)
            img.thumbnail((450, 400))
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo, text="")
            self.img_label.image = photo
        except Exception as e:
            self.log(f"Cannot load image {image_path}: {e}\n")

    # -----------------------------------------------------------------
    # Tab 7: Assets Query
    # -----------------------------------------------------------------
    def _setup_tab_assets(self):
        tab = ttk.Frame(self.script_notebook, padding=15)
        self.script_notebook.add(tab, text="")

        self.asset_title_lbl = ttk.Label(tab, text="", font=("TkDefaultFont", 11, "bold"))
        self.asset_title_lbl.pack(anchor=tk.W, pady=(0, 10))

        f_query = ttk.Frame(tab)
        f_query.pack(fill=tk.X, pady=5)
        self.asset_regex_lbl = ttk.Label(f_query, text="")
        self.asset_regex_lbl.pack(side=tk.LEFT, padx=(0, 10))
        self.asset_regex_entry = ttk.Entry(f_query, width=30)
        self.asset_regex_entry.insert(0, ".*Tree.*")
        self.asset_regex_entry.pack(side=tk.LEFT, padx=5)

        self.asset_btn_query = ttk.Button(f_query, text="", command=self.run_list_assets)
        self.asset_btn_query.pack(side=tk.LEFT, padx=5)
        self.asset_btn_term = ttk.Button(f_query, text="", command=lambda: self.run_list_assets(terminal_mode=True))
        self.asset_btn_term.pack(side=tk.LEFT, padx=5)

        self.asset_res_frame = ttk.LabelFrame(tab, text="", padding=5)
        self.asset_res_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.asset_text = tk.Text(self.asset_res_frame, bg="#252526", fg="#dcdcdc", font=("Monospace", 10))
        sb = ttk.Scrollbar(self.asset_res_frame, orient=tk.VERTICAL, command=self.asset_text.yview)
        self.asset_text.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
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
            messagebox.showwarning(self.t("dialog_busy_title"), self.t("dialog_busy_msg"))
            return

        env = os.environ.copy()
        env["PATH"] = f"{VENV_PYTHON.parent}:{env.get('PATH', '')}"

        self.log(f"\n[EXEC] cwd={cwd}\n[CMD] {' '.join(cmd_args)}\n\n")
        script_label = cmd_args[1] if len(cmd_args)>1 else cmd_args[0]
        self.script_status_label.config(text=self.t("task_running").format(script_label), foreground="#007acc")
        self.btn_stop_script.config(state=tk.NORMAL)

        self.main_notebook.select(self.log_tab)

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
                self.after(0, lambda: self.script_status_label.config(text=self.t("task_idle"), foreground="green"))
                self.after(0, lambda: self.btn_stop_script.config(state=tk.DISABLED))
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
        map_idx = max(0, self.map_combo.current())
        map_key, project_path = MAP_PROJECTS_DATA[map_idx]
        map_display = self.t(map_key)

        cmd = [str(UNREAL_EDITOR_PATH), str(project_path), "-ResX=1280", "-ResY=720", "-WINDOWED"]
        if self.game_mode_var.get():
            cmd.append("-game")

        self.log(f"\n[SYSTEM] Launching Unreal Engine 5: {map_display}\n")
        try:
            self.ue5_process = subprocess.Popen(cmd)
            self.log(f"[SYSTEM] Unreal Engine PID: {self.ue5_process.pid}\n")
            self.ue_status_label.config(text=self.t("ue_status_starting"), foreground="orange")
        except Exception as e:
            self.log(f"[ERROR] Launching Unreal Engine failed: {e}\n")
            messagebox.showerror(self.t("dialog_err_title"), f"Launch Unreal Engine failed:\n{e}")

    def stop_unreal(self):
        self.log("\n[SYSTEM] Killing Unreal Engine processes...\n")
        subprocess.run(["pkill", "-9", "-f", "UnrealEditor"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "Blocks.uproject"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "ForestDomeEnv.uproject"], capture_output=True)
        self.ue5_process = None
        self.is_ue5_running = False
        self.ue_status_label.config(text=self.t("ue_status_stopped"), foreground="red")

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
                self.px4_status_label.config(text=self.t("px4_status_starting"), foreground="orange")
            else:
                self.log(f"[ERROR] Launching PX4 container failed: {res.stderr}\n")
        except Exception as e:
            self.log(f"[ERROR] PX4 container execution error: {e}\n")

    def stop_px4(self):
        self.log("\n[SYSTEM] Stopping PX4 Docker Container...\n")
        subprocess.run(["docker", "stop", "px4_sitl_gui_container"], capture_output=True)
        self.is_px4_running = False
        self.px4_status_label.config(text=self.t("px4_status_stopped"), foreground="red")

    def clean_restart_environment(self):
        if messagebox.askyesno(self.t("dialog_restart_title"), self.t("dialog_restart_msg")):
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
            self.ue_status_label.config(text=self.t("ue_status_running"), foreground="green")
        else:
            self.ue_status_label.config(text=self.t("ue_status_stopped"), foreground="red")

        if px4_running:
            self.px4_status_label.config(text=self.t("px4_status_running"), foreground="green")
        else:
            self.px4_status_label.config(text=self.t("px4_status_stopped"), foreground="red")

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
