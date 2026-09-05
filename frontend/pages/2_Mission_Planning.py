import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Mission Planning", page_icon="🗓️", layout="wide")

API_URL = "http://localhost:8001"

st.title("Mission Planning")
st.markdown("Schedule new observation opportunities across celestial bodies.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Target Selection")
    
    # Check simulation status
    try:
        status_res = requests.get(f"{API_URL}/api/simulation/status")
        status_data = status_res.json()
        gmat_avail = status_data.get("gmat_available", False)
        active_engine = status_data.get("active_engine", "analytical")
        msg = status_data.get("message", "")
    except:
        gmat_avail, active_engine, msg = False, "analytical", "Backend unreachable"

    if gmat_avail:
        st.success(f"Simulation source: GMAT ({msg})")
        engine_options = ["gmat", "analytical"]
    else:
        st.warning(f"Simulation source: ANALYTICAL FALLBACK ({msg})")
        engine_options = ["analytical"]

    with st.form("planning_form"):
        engine_selection = st.selectbox("Simulation Engine", engine_options)
        body_id = st.selectbox("Celestial Body", ["earth", "moon", "mars"])
        lat = st.number_input("Target Latitude (deg)", min_value=-90.0, max_value=90.0, value=0.0)
        lon = st.number_input("Target Longitude (deg)", min_value=-180.0, max_value=180.0, value=0.0)
        submit = st.form_submit_button("Calculate Visibility Windows")

with col2:
    st.subheader("Opportunities")
    if submit:
        # First, ensure backend is using the requested engine before propagating
        try:
            requests.post(f"{API_URL}/api/simulation/run", json={"engine": engine_selection})
        except:
            pass
            
        with st.spinner("Calculating access times..."):
            try:
                res = requests.post(f"{API_URL}/api/observations/plan", json={
                    "body_id": body_id,
                    "lat": lat,
                    "lon": lon
                })
                if res.status_code == 200:
                    opps = res.json()
                    if opps:
                        st.success(f"Found {len(opps)} opportunities!")
                        df = pd.DataFrame(opps)
                        # Format times for display
                        df['start_time'] = pd.to_datetime(df['start_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        df['end_time'] = pd.to_datetime(df['end_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        st.dataframe(df[['spacecraft_id', 'sensor_id', 'start_time', 'end_time', 'overall_score']], use_container_width=True)
                        
                        # Store in session state so we can query them in SatQuery AI
                        if 'planned_observations' not in st.session_state:
                            st.session_state['planned_observations'] = []
                        
                        # Generate mock Observation IDs for the planned opportunities
                        import uuid
                        for opp in opps:
                            opp['observation_id'] = f"OBS-{uuid.uuid4().hex[:6].upper()}"
                            st.session_state['planned_observations'].append(opp)
                            
                        st.info("Observations added to schedule. You can now analyze them in SatQuery AI.")
                    else:
                        st.warning("No visibility windows found in the current timeframe.")
                else:
                    st.error("Error from backend.")
            except Exception as e:
                st.error("Cannot connect to backend.")
