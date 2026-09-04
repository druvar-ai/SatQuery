import requests
import time

API_URL = "http://localhost:8000"

def setup_demo():
    print("Initializing SatQuery Judge Demo...")
    
    # Check simulation engine availability
    try:
        status = requests.get(f"{API_URL}/api/simulation/status").json()
        engine = "gmat" if status.get("gmat_available") else "analytical"
        print(f"Simulation engine: {status.get('message', 'ANALYTICAL FALLBACK')}")
        # Explicitly set the engine via the run endpoint
        requests.post(f"{API_URL}/api/simulation/run", json={"engine": engine})
    except Exception as e:
        print(f"Warning: could not contact backend for engine status. Defaulting to analytical.")
        engine = "analytical"
        
    # 1. Initialize Demo Scenario
    print("Setting up Earth demo constellation...")
    res = requests.post(f"{API_URL}/api/demo/setup")
    if res.status_code == 200:
        print(res.json().get("message"))
    else:
        print("Failed to setup demo.")
    
    # 2. Advance simulation a few steps
    print(f"Advancing simulation clock to generate initial orbits using {engine.upper()}...")
    for _ in range(5):
        requests.post(f"{API_URL}/api/simulation/step")
        time.sleep(0.5)
        
    print("Demo setup complete! The backend is populated with a 10-satellite Earth constellation.")
    print("You can now open the Streamlit UI to plan observations and query the AI.")

if __name__ == "__main__":
    setup_demo()
