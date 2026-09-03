import os
import sys
import numpy as np
from datetime import datetime, timezone, timedelta

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
    
    earth = get_body("earth")
    epoch = datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=98.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=epoch
    )
    
    ana_prop = AnalyticalPropagator()
    gmat_prop = GMATPropagator()
    
    # 1. Initial state comparison
    print("\n=== INITIAL STATE COMPARISON ===")
    pos_ana, vel_ana, alt_ana = ana_prop.propagate(elements, epoch, earth)
    pos_gmat, vel_gmat, alt_gmat = gmat_prop.propagate(elements, epoch, earth)
    
    print(f"Analytical position: {pos_ana}")
    print(f"GMAT position:       {pos_gmat}")
    print(f"Position error:      {np.linalg.norm(pos_ana - pos_gmat):.6f} km")
    print()
    print(f"Analytical velocity: {vel_ana}")
    print(f"GMAT velocity:       {vel_gmat}")
    print(f"Velocity error:      {np.linalg.norm(vel_ana - vel_gmat):.6f} km/s")
    
    # 2. Propagation comparison over time
    print("\n=== PROPAGATION COMPARISON ===")
    print("Time      | Position Error (km) | Velocity Error (km/s) | Altitude Error (km)")
    print("-" * 80)
    
    intervals_minutes = [0, 1, 10, 30, 60]
    
    for t_min in intervals_minutes:
        target_time = epoch + timedelta(minutes=t_min)
        
        # analytical
        p_a, v_a, a_a = ana_prop.propagate(elements, target_time, earth)
        # gmat
        p_g, v_g, a_g = gmat_prop.propagate(elements, target_time, earth)
        
        pos_err = np.linalg.norm(p_a - p_g)
        vel_err = np.linalg.norm(v_a - v_g)
        alt_err = abs(a_a - a_g)
        
        print(f"{t_min:<9} | {pos_err:<19.6f} | {vel_err:<21.6f} | {alt_err:<19.6f}")

if __name__ == "__main__":
    main()
