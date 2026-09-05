"""
SatQuery Mission Simulation — 3D Orbital Visualization & Playback

This is the primary simulation experience. It displays:
  1. Scenario & status bar (active scenario, body, engine, mission time)
  2. 3D orbital scene (celestial body, trajectories, spacecraft markers)
  3. Playback controls (start/pause/step/reset/speed)
  4. Mission timeline (events with status)
  5. Spacecraft telemetry panel (selected spacecraft details)
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import time
import math

st.set_page_config(page_title="Mission Simulation", page_icon="🛰️", layout="wide")

API_URL = "http://localhost:8000"

# ─────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────

def fetch_simulation_state():
    try:
        return requests.get(f"{API_URL}/api/simulation/state", timeout=3).json()
    except Exception:
        return None

def fetch_spacecraft():
    try:
        return requests.get(f"{API_URL}/api/spacecraft", timeout=3).json()
    except Exception:
        return []

def fetch_spacecraft_state(sc_id):
    try:
        res = requests.get(f"{API_URL}/api/spacecraft/{sc_id}/state", timeout=3)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def fetch_trajectory(sc_id):
    try:
        res = requests.get(f"{API_URL}/api/spacecraft/{sc_id}/trajectory", timeout=3)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def fetch_events():
    try:
        res = requests.get(f"{API_URL}/api/simulation/events", timeout=3)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

def fetch_sim_status():
    try:
        res = requests.get(f"{API_URL}/api/simulation/status", timeout=3)
        return res.json() if res.status_code == 200 else {}
    except Exception:
        return {}

def set_simulation_speed(speed):
    try:
        requests.post(f"{API_URL}/api/simulation/speed", json={"speed": speed}, timeout=3)
    except Exception:
        pass


# ─────────────────────────────────────────────────
# Body visual configuration
# ─────────────────────────────────────────────────

BODY_CONFIG = {
    "earth": {
        "name": "Earth",
        "radius_km": 6378.137,
        "color": "#4A90D9",       # Steel blue
        "color_light": "#B8D4F0", # Light fill
        "ring_color": "#2C5F8A",
        "emoji": "🌍",
    },
    "moon": {
        "name": "Moon",
        "radius_km": 1737.4,
        "color": "#8E8E93",       # Silver gray
        "color_light": "#C7C7CC",
        "ring_color": "#636366",
        "emoji": "🌑",
    },
    "mars": {
        "name": "Mars",
        "radius_km": 3389.5,
        "color": "#C1440E",       # Rust red
        "color_light": "#E8A87C",
        "ring_color": "#8B2500",
        "emoji": "🔴",
    },
}

# Distinct spacecraft colors (high-contrast on white)
SC_COLORS = [
    "#1A73E8",  # Blue
    "#E8710A",  # Orange
    "#0D904F",  # Green
    "#9334E6",  # Purple
    "#D93025",  # Red
    "#137CBD",  # Teal
    "#B31412",  # Dark red
    "#1E8E3E",  # Dark green
    "#A142F4",  # Light purple
    "#F29900",  # Amber
]

# Hohmann-specific colors
HOHMANN_COLORS = {
    "sat-h0": "#D93025",  # Transfer vehicle — red
    "sat-h1": "#1A73E8",  # Parking orbit ref — blue
    "sat-h2": "#0D904F",  # GEO target ref — green
}


# ─────────────────────────────────────────────────
# 3D Scene builder
# ─────────────────────────────────────────────────

def build_celestial_body(body_id: str, fig: go.Figure):
    """Add a wireframe sphere for the celestial body."""
    cfg = BODY_CONFIG.get(body_id, BODY_CONFIG["earth"])
    r = cfg["radius_km"]

    # Sphere surface
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 40)
    x = r * np.outer(np.cos(u), np.sin(v))
    y = r * np.outer(np.sin(u), np.sin(v))
    z = r * np.outer(np.ones(np.size(u)), np.cos(v))

    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, cfg["color_light"]], [1, cfg["color"]]],
        showscale=False,
        opacity=0.5,
        name=cfg["name"],
        hoverinfo="name",
    ))

    # Equatorial reference ring
    theta = np.linspace(0, 2 * np.pi, 120)
    ring_r = r * 1.005  # Just above surface
    fig.add_trace(go.Scatter3d(
        x=ring_r * np.cos(theta),
        y=ring_r * np.sin(theta),
        z=np.zeros(120),
        mode="lines",
        line=dict(color=cfg["ring_color"], width=3),
        name="Equator",
        hoverinfo="name",
        showlegend=False,
    ))

    return r


def build_scene(fig: go.Figure, body_id: str, body_radius: float):
    """Configure the 3D scene layout for bright-white technical look."""
    # Camera distance: ~3x body radius for good overview
    cam_dist = body_radius * 3.5

    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title=dict(text="X (km)", font=dict(size=11, color="#555")),
                showbackground=False,
                showgrid=True,
                gridcolor="rgba(200,200,200,0.4)",
                zeroline=True,
                zerolinecolor="rgba(150,150,150,0.5)",
                zerolinewidth=1,
                tickfont=dict(size=9, color="#888"),
            ),
            yaxis=dict(
                title=dict(text="Y (km)", font=dict(size=11, color="#555")),
                showbackground=False,
                showgrid=True,
                gridcolor="rgba(200,200,200,0.4)",
                zeroline=True,
                zerolinecolor="rgba(150,150,150,0.5)",
                zerolinewidth=1,
                tickfont=dict(size=9, color="#888"),
            ),
            zaxis=dict(
                title=dict(text="Z (km)", font=dict(size=11, color="#555")),
                showbackground=False,
                showgrid=True,
                gridcolor="rgba(200,200,200,0.4)",
                zeroline=True,
                zerolinecolor="rgba(150,150,150,0.5)",
                zerolinewidth=1,
                tickfont=dict(size=9, color="#888"),
            ),
            bgcolor="white",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0.8),
                up=dict(x=0, y=0, z=1),
            ),
            aspectmode="data",
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(r=10, l=10, b=10, t=10),
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.98,
            xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(200,200,200,0.5)",
            borderwidth=1,
            font=dict(size=11),
        ),
        height=600,
    )


def add_trajectory(fig, sc_id, traj_data, color, name):
    """Add an orbital trajectory line to the scene."""
    pos_arr = np.array(traj_data["position_km"])
    if len(pos_arr) == 0:
        return
    fig.add_trace(go.Scatter3d(
        x=pos_arr[:, 0], y=pos_arr[:, 1], z=pos_arr[:, 2],
        mode="lines",
        line=dict(width=3, color=color),
        opacity=0.6,
        name=f"{name} trajectory",
        hoverinfo="name",
    ))


def add_spacecraft_marker(fig, sc_state, name, color, selected=False):
    """Add a spacecraft marker at its current position."""
    pos = sc_state.get("position_km", [0, 0, 0])
    size = 8 if selected else 5
    symbol = "diamond" if selected else "circle"

    fig.add_trace(go.Scatter3d(
        x=[pos[0]], y=[pos[1]], z=[pos[2]],
        mode="markers+text",
        marker=dict(
            size=size,
            symbol=symbol,
            color=color,
            line=dict(width=1, color="#333"),
        ),
        text=[name],
        textposition="top center",
        textfont=dict(size=10, color="#333"),
        name=name,
        hovertemplate=(
            f"<b>{name}</b><br>"
            f"X: %{{x:.1f}} km<br>"
            f"Y: %{{y:.1f}} km<br>"
            f"Z: %{{z:.1f}} km<br>"
            f"Alt: {sc_state.get('altitude_km', 0):.1f} km"
            "<extra></extra>"
        ),
    ))


# ─────────────────────────────────────────────────
# Page content
# ─────────────────────────────────────────────────

st.title("🛰️ Mission Simulation")

state = fetch_simulation_state()
if not state:
    st.error("⚠ Cannot connect to backend. Start the API server: `uvicorn satquery.backend.api.main:app --port 8001`")
    st.stop()

clock = state.get("clock", {})
is_running = clock.get("running", False)
sim_time_str = clock.get("current_time", "Unknown")
sim_speed = clock.get("speed", 1.0)
scenario_info = state.get("active_scenario", None)

# Parse sim time
try:
    sim_time = pd.to_datetime(sim_time_str)
except Exception:
    sim_time = datetime.utcnow()

# ─── SCENARIO STATUS BAR ───
if scenario_info:
    body_id = scenario_info.get("celestial_body_id", "earth")
    body_cfg = BODY_CONFIG.get(body_id, BODY_CONFIG["earth"])
    sim_status = fetch_sim_status()
    engine_label = sim_status.get("active_engine", "analytical").upper()

    cols = st.columns([3, 2, 2, 2, 2])
    cols[0].markdown(f"**{body_cfg['emoji']} {scenario_info['name']}**")
    cols[1].markdown(f"Body: **{body_cfg['name']}**")
    cols[2].markdown(f"Engine: **{engine_label}**")
    cols[3].markdown(f"Status: **{'🟢 RUNNING' if is_running else '⏸️ PAUSED'}**")
    cols[4].markdown(f"Time: `{sim_time.strftime('%Y-%m-%d %H:%M:%S')} UTC`")
    st.markdown("---")
else:
    st.info("**No scenario loaded.** Use the sidebar to select and load a mission scenario.")
    st.stop()


# ─── FETCH ALL DATA ───
sats = fetch_spacecraft()
states_dict = {}
trajectories = {}

for s in sats:
    sc_id = s["spacecraft_id"]
    sc_state = fetch_spacecraft_state(sc_id)
    if sc_state:
        states_dict[sc_id] = sc_state
    traj = fetch_trajectory(sc_id)
    if traj:
        trajectories[sc_id] = traj

events = fetch_events()


# ─── 3D ORBITAL VISUALIZATION ───
fig = go.Figure()

# Draw celestial body
body_radius = build_celestial_body(body_id, fig)

# Determine if this is a Hohmann scenario for special coloring
is_hohmann = scenario_info.get("scenario_id", "") == "hohmann_transfer" if scenario_info else False

# Track selected spacecraft
if "selected_sc_idx" not in st.session_state:
    st.session_state.selected_sc_idx = 0

selected_sc_name = None
if sats:
    sel_idx = st.session_state.selected_sc_idx
    if sel_idx >= len(sats):
        sel_idx = 0
    selected_sc_name = sats[sel_idx]["name"]

# Draw trajectories and spacecraft
for i, s in enumerate(sats):
    sc_id = s["spacecraft_id"]
    name = s["name"]

    # Color selection
    if is_hohmann and sc_id in HOHMANN_COLORS:
        color = HOHMANN_COLORS[sc_id]
    else:
        color = SC_COLORS[i % len(SC_COLORS)]

    # Trajectory
    if sc_id in trajectories:
        add_trajectory(fig, sc_id, trajectories[sc_id], color, name)

    # Spacecraft marker
    if sc_id in states_dict:
        is_selected = (name == selected_sc_name)
        add_spacecraft_marker(fig, states_dict[sc_id], name, color, selected=is_selected)

# Configure scene
build_scene(fig, body_id, body_radius)

st.plotly_chart(fig, use_container_width=True, key="sim_3d")


# ─── PLAYBACK CONTROLS ───
st.markdown("---")
ctrl_cols = st.columns([1, 1, 1, 1, 0.5, 2])

if ctrl_cols[0].button("▶ Start", disabled=is_running, use_container_width=True, type="primary" if not is_running else "secondary"):
    requests.post(f"{API_URL}/api/simulation/start", timeout=3)
    st.rerun()

if ctrl_cols[1].button("⏸ Pause", disabled=not is_running, use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/stop", timeout=3)
    st.rerun()

if ctrl_cols[2].button("⏭ Step", use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/step", timeout=3)
    st.rerun()

if ctrl_cols[3].button("↻ Reset", use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/reset", timeout=3)
    st.rerun()

# Speed control
speeds = [1.0, 10.0, 60.0, 300.0, 600.0, 1800.0, 3600.0]
speed_labels = {1.0: "1x", 10.0: "10x", 60.0: "1 min/s", 300.0: "5 min/s", 600.0: "10 min/s", 1800.0: "30 min/s", 3600.0: "1 hr/s"}
speed_idx = speeds.index(sim_speed) if sim_speed in speeds else 0
selected_speed = ctrl_cols[5].selectbox(
    "Playback Speed",
    speeds,
    index=speed_idx,
    format_func=lambda x: speed_labels.get(x, f"{x}x"),
    label_visibility="collapsed",
)
if selected_speed != sim_speed:
    set_simulation_speed(selected_speed)
    st.rerun()


# ─── MISSION TIME PROGRESS ───
try:
    start_t = pd.to_datetime(clock.get("start_time"))
    end_t = pd.to_datetime(clock.get("end_time"))
    total_sec = max((end_t - start_t).total_seconds(), 1)
    elapsed_sec = (sim_time - start_t).total_seconds()
    progress = min(max(elapsed_sec / total_sec, 0.0), 1.0)
    
    time_cols = st.columns([1, 6, 1])
    time_cols[0].caption(start_t.strftime("%H:%M:%S"))
    time_cols[1].progress(progress, text=f"Mission elapsed: {elapsed_sec:.0f}s / {total_sec:.0f}s ({progress*100:.1f}%)")
    time_cols[2].caption(end_t.strftime("%H:%M:%S"))
except Exception:
    pass


# ─── MISSION EVENTS & TELEMETRY ───
st.markdown("---")
col_events, col_telemetry = st.columns([1, 1])

with col_events:
    st.subheader("📋 Mission Events")
    if events:
        for ev in events:
            icon = ev.get("status_icon", "○")
            status = ev.get("status", "upcoming")
            name = ev.get("name", "")
            desc = ev.get("description", "")
            t_sec = ev.get("time_from_epoch_sec", 0)

            # Format time
            if t_sec >= 3600:
                time_label = f"T+{t_sec/3600:.1f}h"
            elif t_sec > 0:
                time_label = f"T+{t_sec:.0f}s"
            else:
                time_label = "T+0"

            # Color based on status
            if status == "completed":
                st.markdown(f"`{icon}` ~~{name}~~ — {time_label}")
            elif status == "active":
                st.markdown(f"**`{icon}` {name}** — {time_label}  \n_{desc}_")
            else:
                st.markdown(f"`{icon}` {name} — {time_label}")
    else:
        st.caption("No mission events defined for this scenario.")

with col_telemetry:
    st.subheader("📡 Spacecraft Telemetry")

    if sats:
        # Spacecraft selector
        sc_names = [s["name"] for s in sats]
        selected_name = st.selectbox(
            "Select Spacecraft",
            sc_names,
            index=st.session_state.selected_sc_idx,
            key="sc_selector",
        )
        # Update selection index
        new_idx = sc_names.index(selected_name)
        if new_idx != st.session_state.selected_sc_idx:
            st.session_state.selected_sc_idx = new_idx
            st.rerun()

        selected_sc = sats[new_idx]
        sc_id = selected_sc["spacecraft_id"]

        if sc_id in states_dict:
            s_state = states_dict[sc_id]
            pos = s_state.get("position_km", [0, 0, 0])
            vel = s_state.get("velocity_km_s", [0, 0, 0])
            alt = s_state.get("altitude_km", 0)
            source = s_state.get("simulation_source", "UNKNOWN")
            body_name = s_state.get("celestial_body_id", "earth").capitalize()

            # Speed magnitude
            speed_mag = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
            # Distance from center
            r_mag = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)

            # Header info
            info_cols = st.columns(3)
            info_cols[0].metric("Body", body_name)
            info_cols[1].metric("Source", source)
            info_cols[2].metric("Altitude", f"{alt:.1f} km")

            # Position and velocity
            pv_cols = st.columns(2)
            with pv_cols[0]:
                st.markdown("**Position (km)**")
                st.code(f"X: {pos[0]:>12.2f}\nY: {pos[1]:>12.2f}\nZ: {pos[2]:>12.2f}\n──────────────\nR: {r_mag:>12.2f}", language=None)
            with pv_cols[1]:
                st.markdown("**Velocity (km/s)**")
                st.code(f"VX: {vel[0]:>11.4f}\nVY: {vel[1]:>11.4f}\nVZ: {vel[2]:>11.4f}\n──────────────\n|V|: {speed_mag:>10.4f}", language=None)

            # Sensor info
            sensors = selected_sc.get("sensors", [])
            if sensors:
                sensor = sensors[0]
                st.markdown(f"**Sensor:** `{sensor.get('sensor_type', 'unknown').upper()}` — FOV: {sensor.get('field_of_view_deg', 0)}° — Status: `{sensor.get('operational_status', 'unknown')}`")
        else:
            st.warning("No state data available. Step the simulation to generate initial states.")
    else:
        st.caption("No spacecraft in current scenario.")


# ─── AUTO-STEP WHEN RUNNING ───
if is_running:
    requests.post(f"{API_URL}/api/simulation/step", timeout=3)
    time.sleep(0.8)
    st.rerun()
