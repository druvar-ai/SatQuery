import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Overview", page_icon="🌍", layout="wide")

API_URL = "http://localhost:8000"

st.title("Constellation Overview")

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

state = fetch_simulation_state()
if not state:
    st.error("Cannot connect to backend.")
else:
    clock = state.get("clock", {})
    st.markdown(f"**Current Simulation Time:** `{clock.get('current_time')}`")
    st.markdown(f"**Simulation Engine:** `{state.get('engine')}`")

st.markdown("---")
st.subheader("Spacecraft Fleet")

sats = fetch_spacecraft()
if not sats:
    st.info("No spacecraft in constellation. Run the demo setup script.")
else:
    df = pd.DataFrame(sats)
    st.dataframe(df, use_container_width=True)
    
    # Very basic Map (ScatterGeo) if earth
    earth_sats = [s for s in sats if s.get("celestial_body_id") == "earth"]
    if earth_sats:
        st.subheader("Earth Orbit Overview (2D Projection)")
        # Just randomly distributing them for visual effect in this basic UI MVP since 
        # actual position in lat/lon requires full coordinate transform logic.
        # But wait! We can fetch their states to get position.
        
        lats, lons, names = [], [], []
        for s in earth_sats:
            try:
                state_res = requests.get(f"{API_URL}/api/spacecraft/{s['spacecraft_id']}/state")
                if state_res.status_code == 200:
                    sc_state = state_res.json()
                    pos = sc_state.get("position_km", [0,0,0])
                    # Crude approximation for visualization only: 
                    import math
                    r = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
                    lat = math.degrees(math.asin(pos[2]/r)) if r > 0 else 0
                    lon = math.degrees(math.atan2(pos[1], pos[0]))
                    lats.append(lat)
                    lons.append(lon)
                    names.append(s['name'])
            except:
                pass
                
        if lats:
            map_df = pd.DataFrame({"lat": lats, "lon": lons, "name": names})
            fig = px.scatter_geo(map_df, lat='lat', lon='lon', text='name', projection="natural earth")
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
