#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard / Ground Control Station UI for DroneDigitalTwin
Real-Time Telemetry Visualization connecting to ProjectAirSim / PX4.
"""

import math
import sys
import os
import tkinter as tk
import customtkinter as ctk
import pynng
from pathlib import Path
from sys import platform

# Add projectairsim python package to path (gui_demo -> python -> client/python)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCENE_ID = "SceneBasicDrone"
DRONE_NAME = "Drone1"

try:
    from projectairsim import ProjectAirSimClient
    from projectairsim.utils import projectairsim_log
except ImportError:
    ProjectAirSimClient = None
    projectairsim_log = None


class ServicesOnlyClient(ProjectAirSimClient):
    """Connects only to the request/response services socket.

    ProjectAirSim's topic socket is nng Pair0 (strictly 1:1), so a second
    client would steal the live topic stream away from the active flight
    script. A passive telemetry dashboard only needs the services socket, so
    we never dial the topics socket and never interfere with the running
    script (no scene reload, no subscriptions).
    """

    def connect(self):
        projectairsim_log().info(
            f"Connecting services-only to {self.address}:{self.port_services}"
        )
        self.socket_services = pynng.Req0(
            recv_timeout=3000, send_timeout=1000, resend_time=-1
        )
        self.request_id = self.request_id_generator()
        if "win" in platform:
            self.socket_services.dial(
                f"tcp://{self.address}:{self.port_services}".encode(), block=True
            )
        else:
            self.socket_services.dial(
                address=f"tcp://{self.address}:{self.port_services}", block=True
            )
        self.state = True

    def disconnect(self):
        projectairsim_log().info("Disconnecting services-only client.")
        self.state = False
        if self.socket_services is not None:
            self.socket_services.close()

    def get_ground_truth_kinematics(self):
        """Request ground-truth kinematics for the drone directly via services."""
        kinematics_req = {
            "method": f"/Sim/{SCENE_ID}/robots/{DRONE_NAME}/GetGroundTruthKinematics",
            "params": {},
            "version": 1.0,
        }
        return self.request(kinematics_req)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CircularGauge(ctk.CTkCanvas):
    def __init__(self, master, title="Gauge", min_val=0, max_val=100, unit="", size=220, start_angle=225, extent=-270, **kwargs):
        super().__init__(master, width=size, height=size, bg="#1a1a1a", highlightthickness=0, **kwargs)
        self.size = size
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.start_angle = start_angle
        self.extent = extent
        self.value = min_val

        self.cx = size / 2
        self.cy = size / 2
        self.radius = size / 2.5
        
        self.draw_static_elements()
        self.draw_needle()

    def draw_static_elements(self):
        # Draw background circle
        self.create_oval(self.cx - self.radius, self.cy - self.radius, 
                         self.cx + self.radius, self.cy + self.radius, 
                         outline="#333333", width=4)
        
        # Draw ticks and labels
        num_ticks = 10
        for i in range(num_ticks + 1):
            val = self.min_val + (self.max_val - self.min_val) * (i / num_ticks)
            angle_deg = self.start_angle + self.extent * (i / num_ticks)
            angle_rad = math.radians(angle_deg)
            
            # Tick positions
            inner_r = self.radius - 10
            outer_r = self.radius
            x1 = self.cx + inner_r * math.cos(angle_rad)
            y1 = self.cy - inner_r * math.sin(angle_rad)
            x2 = self.cx + outer_r * math.cos(angle_rad)
            y2 = self.cy - outer_r * math.sin(angle_rad)
            
            self.create_line(x1, y1, x2, y2, fill="#ffffff", width=2)
            
            # Text positions
            text_r = self.radius - 25
            tx = self.cx + text_r * math.cos(angle_rad)
            ty = self.cy - text_r * math.sin(angle_rad)
            self.create_text(tx, ty, text=f"{int(val)}", fill="#aaaaaa", font=("Arial", 9))

        # Title and Unit
        self.create_text(self.cx, self.cy - self.radius - 15, text=self.title, fill="#ffffff", font=("Arial", 12, "bold"))
        self.create_text(self.cx, self.cy + self.radius / 2, text=self.unit, fill="#3b8ed0", font=("Arial", 10))

    def set_value(self, value):
        self.value = max(self.min_val, min(self.max_val, value))
        self.delete("needle")
        self.delete("val_text")
        self.draw_needle()

    def draw_needle(self):
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val) if self.max_val != self.min_val else 0
        angle_deg = self.start_angle + self.extent * ratio
        angle_rad = math.radians(angle_deg)

        needle_length = self.radius - 15
        nx = self.cx + needle_length * math.cos(angle_rad)
        ny = self.cy - needle_length * math.sin(angle_rad)

        # Draw needle
        self.create_line(self.cx, self.cy, nx, ny, fill="#ff4d4d", width=3, arrow=tk.LAST, tags="needle")
        self.create_oval(self.cx - 5, self.cy - 5, self.cx + 5, self.cy + 5, fill="#ff4d4d", tags="needle")
        
        # Draw current value text
        self.create_text(self.cx, self.cy + 25, text=f"{self.value:.1f}", fill="#ffffff", font=("Arial", 14, "bold"), tags="val_text")


class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DroneDigitalTwin Live Telemetry Dashboard")
        self.geometry("620x650")
        self.configure(fg_color="#1a1a1a")

        # Connection status label
        self.status_label = ctk.CTkLabel(self, text="● Status: Connecting to Drone Telemetry...", font=("Arial", 13, "bold"), text_color="orange")
        self.status_label.pack(pady=(15, 5))

        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        grid_frame.grid_columnconfigure((0, 1), weight=1)
        grid_frame.grid_rowconfigure((0, 1), weight=1)

        # 1. Altitude Gauge
        self.alt_gauge = CircularGauge(grid_frame, title="Altitude", min_val=0, max_val=100, unit="meters")
        self.alt_gauge.grid(row=0, column=0, padx=15, pady=15)

        # 2. Air Speed Gauge
        self.speed_gauge = CircularGauge(grid_frame, title="Air Speed", min_val=0, max_val=30, unit="m/s")
        self.speed_gauge.grid(row=0, column=1, padx=15, pady=15)

        # 3. Course / Heading Gauge
        self.course_gauge = CircularGauge(grid_frame, title="Heading / Yaw", min_val=0, max_val=360, unit="deg", start_angle=90, extent=-360)
        self.course_gauge.grid(row=1, column=0, padx=15, pady=15)

        # 4. Distance to Origin Gauge
        self.dist_gauge = CircularGauge(grid_frame, title="Distance to Origin", min_val=0, max_val=500, unit="meters")
        self.dist_gauge.grid(row=1, column=1, padx=15, pady=15)

        self.client = None
        self.is_connected = False

        self.targets = {"alt": 0.0, "speed": 0.0, "course": 0.0, "dist": 0.0}
        self.current_vals = {"alt": 0.0, "speed": 0.0, "course": 0.0, "dist": 0.0}

        self.poll_telemetry()
        self.animate_gauges()

    def poll_telemetry(self):
        """Poll real ground-truth kinematics & telemetry from ProjectAirSim client."""
        next_interval = 100

        if not self.is_connected:
            next_interval = 2000
            try:
                if ProjectAirSimClient:
                    self.client = ServicesOnlyClient()
                    self.client.connect()
                    self.is_connected = True
                    self.status_label.configure(text="● Status: CONNECTED (Live Drone Telemetry)", text_color="#2ECC71")
                    next_interval = 500
            except Exception:
                try:
                    if self.client is not None:
                        self.client.disconnect()
                except Exception:
                    pass
                self.is_connected = False
                self.client = None
                self.status_label.configure(text="● Status: STANDBY (Waiting for Drone / Simulation)", text_color="#E74C3C")

        if self.is_connected and self.client:
            try:
                kinematics = self.client.get_ground_truth_kinematics()
                if kinematics and "pose" in kinematics:
                    pos = kinematics["pose"]["position"]
                    vel = kinematics["twist"].get("linear", {"x": 0, "y": 0, "z": 0})
                    orient = kinematics["pose"].get("orientation", {"w": 1, "x": 0, "y": 0, "z": 0})

                    # Altitude: -Z (NED frame: Z is down, so altitude is positive up)
                    alt = max(0.0, -float(pos.get("z", 0.0)))

                    # Speed: magnitude of (vx, vy, vz)
                    vx, vy, vz = float(vel.get("x", 0.0)), float(vel.get("y", 0.0)), float(vel.get("z", 0.0))
                    speed = math.sqrt(vx*vx + vy*vy + vz*vz)

                    # Distance from origin (0,0,0)
                    px, py = float(pos.get("x", 0.0)), float(pos.get("y", 0.0))
                    dist = math.sqrt(px*px + py*py)

                    # Yaw heading from Quaternion (w, x, y, z)
                    qw, qx, qy, qz = float(orient.get("w", 1.0)), float(orient.get("x", 0.0)), float(orient.get("y", 0.0)), float(orient.get("z", 0.0))
                    siny_cosp = 2 * (qw * qz + qx * qy)
                    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
                    yaw_rad = math.atan2(siny_cosp, cosy_cosp)
                    yaw_deg = math.degrees(yaw_rad) % 360

                    self.targets["alt"] = alt
                    self.targets["speed"] = speed
                    self.targets["course"] = yaw_deg
                    self.targets["dist"] = dist
            except Exception:
                try:
                    self.client.disconnect()
                except Exception:
                    pass
                self.is_connected = False
                self.client = None
                self.status_label.configure(text="● Status: DISCONNECTED (Drone Connection Lost)", text_color="#E74C3C")

        # Poll telemetry at next_interval (500ms when connected, 2000ms when offline)
        self.after(next_interval, self.poll_telemetry)

    def animate_gauges(self):
        """Smoothly interpolate current values towards real telemetry targets."""
        smooth_factor = 0.25
        
        for key in self.current_vals:
            diff = self.targets[key] - self.current_vals[key]
            # Handle 360 deg wrap around for course / heading
            if key == "course":
                if diff > 180: diff -= 360
                elif diff < -180: diff += 360
                
            self.current_vals[key] += diff * smooth_factor
            
            if key == "course":
                self.current_vals[key] %= 360

        self.alt_gauge.set_value(self.current_vals["alt"])
        self.speed_gauge.set_value(self.current_vals["speed"])
        self.course_gauge.set_value(self.current_vals["course"])
        self.dist_gauge.set_value(self.current_vals["dist"])

        # Update visual frame at 30 FPS
        self.after(33, self.animate_gauges)


if __name__ == "__main__":
    app = DashboardApp()
    app.mainloop()
