import requests
import time

API_URL = "http://localhost:8000"

def setup_demo():
    print("Initializing SatQuery Judge Demo...")
    
    # 1. Initialize Demo Scenario
    print("Setting up Earth demo constellation...")
    res = requests.post(f"{API_URL}/api/demo/setup")
    if res.status_code == 200:
        print(res.json().get("message"))
    else:
        print("Failed to setup demo.")
    
    # 2. Advance simulation a few steps
    print("Advancing simulation clock to generate initial orbits...")
    for _ in range(5):
        requests.post(f"{API_URL}/api/simulation/step")
        time.sleep(0.5)
        
    print("Demo setup complete! The backend is populated with a 10-satellite Earth constellation.")
    print("You can now open the Streamlit UI to plan observations and query the AI.")

if __name__ == "__main__":
    setup_demo()
