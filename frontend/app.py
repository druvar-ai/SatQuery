import streamlit as st
import requests

st.set_page_config(
    page_title="SatQuery Mission Control",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8001"

st.sidebar.title("🛰️ SatQuery")
st.sidebar.markdown("---")

# Scenario Selector
st.sidebar.subheader("Mission Scenario")

# Fetch available scenarios
try:
    scenarios_res = requests.get(f"{API_URL}/api/scenarios", timeout=3)
    scenarios = scenarios_res.json() if scenarios_res.status_code == 200 else []
except Exception:
    scenarios = []

if scenarios:
    scenario_options = {s["scenario_id"]: s["name"] for s in scenarios}
    
    # Get current active scenario
    try:
        state_res = requests.get(f"{API_URL}/api/simulation/state", timeout=3)
        state_data = state_res.json() if state_res.status_code == 200 else {}
        active = state_data.get("active_scenario", {})
        current_scenario = active.get("scenario_id", None) if active else None
    except Exception:
        current_scenario = None
    
    scenario_ids = list(scenario_options.keys())
    current_idx = scenario_ids.index(current_scenario) if current_scenario in scenario_ids else 0
    
    selected_scenario = st.sidebar.selectbox(
        "Select Scenario",
        scenario_ids,
        index=current_idx,
        format_func=lambda x: scenario_options.get(x, x),
    )
    
    if st.sidebar.button("Load Scenario", use_container_width=True, type="primary"):
        try:
            res = requests.post(f"{API_URL}/api/demo/setup", json={"scenario_id": selected_scenario}, timeout=30)
            if res.status_code == 200:
                st.sidebar.success(f"✓ Loaded: {scenario_options[selected_scenario]}")
                st.rerun()
            else:
                st.sidebar.error("Failed to load scenario")
        except Exception as e:
            st.sidebar.error(f"Backend error: {e}")
else:
    st.sidebar.warning("Backend not running")

st.sidebar.markdown("---")

# Simulation engine status
try:
    status_res = requests.get(f"{API_URL}/api/simulation/status", timeout=3)
    if status_res.status_code == 200:
        status = status_res.json()
        engine = status.get("active_engine", "unknown").upper()
        gmat_avail = status.get("gmat_available", False)
        if gmat_avail:
            st.sidebar.success(f"Engine: **{engine}** (GMAT available)")
        else:
            st.sidebar.info(f"Engine: **{engine}** (GMAT not found)")
except Exception:
    pass

st.sidebar.markdown("---")
st.sidebar.caption(
    "SatQuery simulates multi-spacecraft mission operations and autonomously plans "
    "observation opportunities. It does not control real satellites."
)

st.title("SatQuery Mission Control")
st.markdown(
    """
    Welcome to the SatQuery Mission Control Dashboard.
    
    Navigate using the sidebar:
    - **1 Mission Simulation** — 3D orbital visualization, playback, telemetry
    - **2 Mission Planning** — Schedule observation opportunities
    - **3 SatQuery AI** — Multi-modal satellite observation intelligence
    
    **Getting started:** Select a mission scenario in the sidebar and click **Load Scenario**.
    """
)
