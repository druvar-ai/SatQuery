import os
import sys
import numpy as np
from datetime import datetime, timezone

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.celestial.body import get_body
from satquery.backend.orbit.propagator import AnalyticalPropagator
from satquery.backend.simulation.gmat.gmat_propagator import GMATPropagator
from satquery.backend.simulation.gmat.gmat_runner import GMATRunner

def main():
    print("=== SATQUERY PROPAGATOR COMPARISON ===")
    
    if not GMATRunner.is_available():
        print("ERROR: GMAT is not available. Please set GMAT_BIN environment variable.")
        sys.exit(1)
        
    print(f"GMAT detected at: {GMATRunner.get_gmat_bin()}")
    
    # Setup test condition
    earth = get_body("earth")
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    target_time = datetime(2026, 1, 1, 1, 0, 0, tzinfo=timezone.utc) # + 1 hour
    
    elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=98.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=epoch
    )
    
    print("\n--- Initial Conditions ---")
    print(f"SMA: 7000 km, INC: 98 deg")
    print(f"Epoch: {epoch}")
    print(f"Target: {target_time}")
    
    # Analytical
    print("\n--- Analytical Propagator ---")
    ana_prop = AnalyticalPropagator()
    pos_ana, vel_ana, alt_ana = ana_prop.propagate(elements, target_time, earth)
    print(f"Position (km): {pos_ana}")
    print(f"Velocity (km/s): {vel_ana}")
    print(f"Altitude (km): {alt_ana:.3f}")
    
    # GMAT
    print("\n--- GMAT Propagator ---")
    gmat_prop = GMATPropagator()
    pos_gmat, vel_gmat, alt_gmat = gmat_prop.propagate(elements, target_time, earth)
    print(f"Position (km): {pos_gmat}")
    print(f"Velocity (km/s): {vel_gmat}")
    print(f"Altitude (km): {alt_gmat:.3f}")
    
    # Comparison
    print("\n--- Comparison ---")
    pos_diff = np.linalg.norm(pos_ana - pos_gmat)
    vel_diff = np.linalg.norm(vel_ana - vel_gmat)
    alt_diff = abs(alt_ana - alt_gmat)
    
    print(f"Position Absolute Error: {pos_diff:.6f} km")
    print(f"Velocity Absolute Error: {vel_diff:.6f} km/s")
    print(f"Altitude Absolute Error: {alt_diff:.6f} km")
    
    print("\nNote: Expected differences exist due to frame conversions and Earth body constants.")

if __name__ == "__main__":
    main()
