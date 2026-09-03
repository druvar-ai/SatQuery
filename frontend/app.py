import streamlit as st
import requests

st.set_page_config(
    page_title="SatQuery Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

st.sidebar.title("🛰️ SatQuery Operations")
st.sidebar.markdown("---")

st.sidebar.subheader("Simulation Control")
col1, col2 = st.sidebar.columns(2)

if col1.button("▶️ Start"):
    try:
        requests.post(f"{API_URL}/api/simulation/start")
        st.sidebar.success("Simulation Started")
    except Exception as e:
        st.sidebar.error("Backend not running.")

if col2.button("⏸️ Pause"):
    try:
        requests.post(f"{API_URL}/api/simulation/stop")
        st.sidebar.warning("Simulation Paused")
    except Exception as e:
        st.sidebar.error("Backend not running.")
        
if st.sidebar.button("⏭️ Step (+60s)"):
    try:
        res = requests.post(f"{API_URL}/api/simulation/step")
        if res.status_code == 200:
            st.sidebar.info(f"Stepped. Current Time: {res.json().get('time')}")
    except Exception:
        pass

st.sidebar.markdown("---")
st.sidebar.info(
    "**Note:** SatQuery simulates multi-spacecraft mission operations and autonomously plans observation opportunities. "
    "It does not control real satellites."
)

st.title("SatQuery Mission Control")
st.markdown(
    """
    Welcome to the SatQuery Mission Control Dashboard.
    
    Please navigate using the sidebar to:
    - **1 Overview**: View the current constellation state.
    - **2 Mission Planning**: Schedule new observation opportunities.
    - **3 SatQuery AI**: Query the intelligence system for multi-modal analysis.
    """
)
