import pytest
import datetime
import numpy as np
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.orbit.propagator import AnalyticalPropagator
from satquery.backend.celestial.body import get_body

def test_analytical_propagator_earth():
    body = get_body("earth")
    elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=45.0,
        raan_deg=10.0,
        arg_periapsis_deg=20.0,
        true_anomaly_deg=30.0,
        epoch=datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    )
    
    propagator = AnalyticalPropagator()
    
    # Propagate to 1 hour later
    target_time = elements.epoch + datetime.timedelta(hours=1)
    pos, vel, alt = propagator.propagate(elements, target_time, body)
    
    assert pos.shape == (3,)
    assert vel.shape == (3,)
    assert isinstance(alt, float)
    assert alt > 0
    assert not np.isnan(pos).any()
    assert not np.isnan(vel).any()

def test_analytical_propagator_mars():
    body = get_body("mars")
    elements = OrbitalElements(
        semi_major_axis_km=4000.0,
        eccentricity=0.01,
        inclination_deg=90.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=datetime.datetime.now(datetime.timezone.utc)
    )
    
    propagator = AnalyticalPropagator()
    target_time = elements.epoch + datetime.timedelta(hours=2)
    pos, vel, alt = propagator.propagate(elements, target_time, body)
    
    assert pos.shape == (3,)
    assert alt > 0
