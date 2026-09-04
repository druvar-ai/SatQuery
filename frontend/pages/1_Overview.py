import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(page_title="Mission Control Overview", page_icon="🌍", layout="wide")

API_URL = "http://localhost:8001"

# --- HELPER FUNCTIONS ---
def fetch_simulation_state():
    try:
        res = requests.get(f"{API_URL}/api/simulation/state")
        return res.json()
    except:
        return None

def fetch_spacecraft():
    try:
        res = requests.get(f"{API_URL}/api/spacecraft")
        return res.json()
    except:
        return []

def fetch_spacecraft_state(sc_id):
    try:
        res = requests.get(f"{API_URL}/api/spacecraft/{sc_id}/state")
        if res.status_code == 200:
            return res.json()
    except:
        return None

# --- HEADER & CONTROLS ---
st.title("🛰️ SatQuery Mission Control")

state = fetch_simulation_state()
if not state:
    st.error("Cannot connect to backend. Please ensure the FastAPI server is running.")
    st.stop()

clock = state.get("clock", {})
is_running = clock.get("running", False)
sim_time_str = clock.get("current_time", "Unknown")

# Top Metrics Row
met1, met2, met3, met4 = st.columns(4)
met1.metric("Simulation Status", "RUNNING" if is_running else "PAUSED")
met2.metric("Simulation Engine", state.get("engine", "Unknown").upper())
met3.metric("Spacecraft Count", state.get("spacecraft_count", 0))
met4.metric("Current Time (UTC)", sim_time_str.split(".")[0].replace("T", " ") if "T" in sim_time_str else sim_time_str)

st.markdown("---")

# Control Bar
st.subheader("Simulation Controls")
c1, c2, c3, c4 = st.columns(4)
if c1.button("▶️ Start Simulation", disabled=is_running, use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/start")
    st.rerun()

if c2.button("⏸️ Pause Simulation", disabled=not is_running, use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/stop")
    st.rerun()

if c3.button("⏭️ Step (+60s)", use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/step")
    st.rerun()

if c4.button("🔄 Reset to Epoch", use_container_width=True):
    requests.post(f"{API_URL}/api/simulation/reset")
    st.rerun()

st.markdown("---")

# --- MAIN VISUALIZATION ---
sats = fetch_spacecraft()

col_map, col_telemetry = st.columns([2, 1])

with col_map:
    st.subheader("Orbital Ground Track (2D Projection)")
    if not sats:
        st.info("No spacecraft in constellation. Run the demo setup script.")
    else:
        lats, lons, names, alts, sensors, bodies = [], [], [], [], [], []
        states_dict = {}
        
        for s in sats:
            sc_id = s['spacecraft_id']
            sc_state = fetch_spacecraft_state(sc_id)
            if sc_state:
                states_dict[sc_id] = sc_state
                pos = sc_state.get("position_km", [0, 0, 0])
                alt = sc_state.get("altitude_km", 0)
                body = sc_state.get("celestial_body_id", "earth")
                
                # Crude cartesian to spherical projection for 2D visualization
                # This assumes ECI/MCI coordinates roughly aligned with equator for visual purposes
                import math
                r = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
                lat = math.degrees(math.asin(pos[2]/r)) if r > 0 else 0
                lon = math.degrees(math.atan2(pos[1], pos[0]))
                
                lats.append(lat)
                lons.append(lon)
                names.append(s['name'])
                alts.append(round(alt, 2))
                sensors.append(sc_state.get("sensor_state", "none"))
                bodies.append(body.capitalize())
        
        if lats:
            map_df = pd.DataFrame({
                "lat": lats, 
                "lon": lons, 
                "Spacecraft": names,
                "Altitude (km)": alts,
                "Sensor": sensors,
                "Body": bodies
            })
            
            fig = px.scatter_geo(
                map_df, 
                lat='lat', 
                lon='lon', 
                hover_name='Spacecraft',
                hover_data={"Altitude (km)": True, "Sensor": True, "Body": True, "lat": False, "lon": False},
                projection="natural earth",
                color="Body"
            )
            
            fig.update_traces(marker=dict(size=12, symbol="star", line=dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(
                margin={"r":0,"t":0,"l":0,"b":0},
                geo=dict(showocean=True, oceancolor="LightBlue", showland=True, landcolor="LightGreen", showcountries=True)
            )
            st.plotly_chart(fig, use_container_width=True)

with col_telemetry:
    st.subheader("Live Telemetry")
    if not sats:
        st.write("Awaiting spacecraft data...")
    else:
        # Select spacecraft to view details
        selected_name = st.selectbox("Select Spacecraft", [s['name'] for s in sats])
        selected_sc = next((s for s in sats if s['name'] == selected_name), None)
        
        if selected_sc and selected_sc['spacecraft_id'] in states_dict:
            s_state = states_dict[selected_sc['spacecraft_id']]
            st.markdown(f"**ID:** `{s_state.get('spacecraft_id')}`")
            st.markdown(f"**Body:** `{s_state.get('celestial_body_id').capitalize()}`")
            st.markdown(f"**Source:** `{s_state.get('simulation_source', 'Unknown')}`")
            
            pos = s_state.get("position_km", [0,0,0])
            vel = s_state.get("velocity_km_s", [0,0,0])
            
            st.markdown("**Position (km):**")
            st.code(f"X: {pos[0]:.2f}\nY: {pos[1]:.2f}\nZ: {pos[2]:.2f}")
            
            st.markdown("**Velocity (km/s):**")
            st.code(f"VX: {vel[0]:.2f}\nVY: {vel[1]:.2f}\nVZ: {vel[2]:.2f}")
            
            st.markdown(f"**Altitude:** `{s_state.get('altitude_km', 0):.2f} km`")

st.markdown("---")
st.subheader("Fleet Status")
if sats:
    fleet_df = pd.DataFrame([
        {
            "ID": s['spacecraft_id'],
            "Name": s['name'],
            "Type": s.get('spacecraft_type', 'unknown'),
            "Body": s.get('celestial_body_id', 'earth').capitalize(),
            "Sensors": ", ".join([sens['sensor_type'] for sens in s.get('sensors', [])])
        } for s in sats
    ])
    st.dataframe(fleet_df, use_container_width=True)

# --- AUTOREFRESH LOOP ---
if is_running:
    # If running, advance simulation step and refresh
    requests.post(f"{API_URL}/api/simulation/step")
    time.sleep(1) # Reasonable UI playback interval (1 frame per second)
    st.rerun()
