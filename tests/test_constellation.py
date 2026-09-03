import pytest
import datetime
from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.spacecraft.model import Spacecraft
from satquery.backend.orbit.elements import OrbitalElements

def test_constellation_manager():
    manager = ConstellationManager()
    
    sc = Spacecraft(
        spacecraft_id="TEST-001",
        name="Test Sat",
        celestial_body_id="earth",
        spacecraft_type="orbiter"
    )
    
    elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.01,
        inclination_deg=45.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=datetime.datetime.now(datetime.timezone.utc)
    )
    
    manager.add_spacecraft(sc, elements)
    assert len(manager.get_all_spacecraft()) == 1
    
    # Test propagation
    manager.propagate_all(datetime.datetime.now(datetime.timezone.utc))
    state = manager.get_state("TEST-001")
    
    assert state is not None
    assert state.altitude_km > 0
    assert len(state.position_km) == 3
    assert len(state.velocity_km_s) == 3
