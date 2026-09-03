import streamlit as st
import requests
import json

st.set_page_config(page_title="SatQuery AI", page_icon="🧠", layout="wide")

API_URL = "http://localhost:8000"

st.title("SatQuery Intelligence")
st.markdown("Natural-language satellite observation queries powered by AI.")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Observation Context")
    if 'planned_observations' in st.session_state and st.session_state['planned_observations']:
        obs_options = {o['observation_id']: f"{o['observation_id']} ({o['spacecraft_id']} via {o['sensor_id']})" for o in st.session_state['planned_observations']}
        selected_obs = st.selectbox("Select Target Observation", options=list(obs_options.keys()), format_func=lambda x: obs_options[x])
    else:
        st.warning("No planned observations found in session. Using fallback ID.")
        selected_obs = "OBS-FALLBACK"
        
    st.markdown("---")
    st.markdown("**Example Queries:**")
    st.code("Analyze this optical image.")
    st.code("What changed in this region?")
    st.code("Perform multimodal fusion analysis.")

with col2:
    st.subheader("Query Interface")
    
    # Display chat history
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🛰️"):
                data = msg["data"]
                
                # Check if multimodal JSON
                try:
                    ans_dict = json.loads(data['answer'])
                    st.markdown("**Multimodal Analysis:**")
                    st.info(f"**Optical:** {ans_dict.get('optical_result', '')}")
                    st.info(f"**SAR:** {ans_dict.get('sar_result', '')}")
                    st.warning(f"**Fusion Interpretation:** {ans_dict.get('fused_interpretation', '')}")
                except json.JSONDecodeError:
                    st.write(data["answer"])
                
                with st.expander("Confidence & Evidence Breakdown"):
                    conf = data.get("confidence", {})
                    st.progress(conf.get("value", 0.0), text=f"Confidence Score: {conf.get('value', 0.0)}")
                    st.markdown(f"**Type:** `{conf.get('type')}` | **Calibrated:** `{conf.get('calibrated')}`")
                    
                    st.markdown("**Evidence Trace:**")
                    for ev in data.get("evidence", []):
                        st.markdown(f"- **{ev['type']}**: {ev['explanation']} *(Score: {ev['score']})*")
                        
                    st.markdown("**Routing Trace:**")
                    st.json(data.get("routing_trace", {}))

    # Input form
    if prompt := st.chat_input("Ask SatQuery..."):
        # Display user msg immediately
        st.chat_message("user").write(prompt)
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant", avatar="🛰️"):
            with st.spinner("Analyzing observation data..."):
                try:
                    res = requests.post(f"{API_URL}/api/analysis/query", json={
                        "query": prompt,
                        "observation_id": selected_obs
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["chat_history"].append({"role": "assistant", "data": data})
                        st.rerun()
                    else:
                        st.error("Error analyzing query.")
                except Exception as e:
                    st.error("Cannot connect to backend.")
