import pytest
import datetime
from satquery.backend.mission.model import Mission, TargetRegion
from satquery.backend.spacecraft.model import Spacecraft
from satquery.backend.sensors.model import Sensor
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.observation.planner import ObservationPlanner

def test_observation_planner():
    constellation = ConstellationManager()
    
    sensor = Sensor(sensor_id="SENS-01", sensor_type="optical", field_of_view_deg=15.0)
    sc = Spacecraft(
        spacecraft_id="SAT-001",
        name="Test Observer",
        celestial_body_id="earth",
        spacecraft_type="orbiter",
        sensors=[sensor]
    )
    
    # Low Earth Orbit
    elements = OrbitalElements(
        semi_major_axis_km=6800.0,
        eccentricity=0.001,
        inclination_deg=90.0,  # Polar orbit
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    )
    constellation.add_spacecraft(sc, elements)
    
    target = TargetRegion(
        target_id="TR-01",
        body_id="earth",
        name="Equator Target",
        latitude_deg=0.0,
        longitude_deg=0.0,
        mission_objective="Observe Equator"
    )
    
    mission = Mission(
        mission_id="M-01",
        name="Test Mission",
        target_body_id="earth",
        spacecraft_ids=["SAT-001"],
        target_regions=[target],
        mission_objective="Test Planner",
        start_time=elements.epoch,
        end_time=elements.epoch + datetime.timedelta(hours=2)
    )
    
    planner = ObservationPlanner(constellation)
    opportunities = planner.calculate_opportunities(
        mission=mission,
        target=target,
        time_window_start=mission.start_time,
        time_window_end=mission.end_time,
        timestep_seconds=60.0
    )
    
    assert isinstance(opportunities, list)
    # With a polar orbit at 0 anomaly and 0 RAAN starting over the equator, 
    # it should be immediately visible or very soon
    assert len(opportunities) > 0
    
    opp = opportunities[0]
    assert opp.spacecraft_id == "SAT-001"
    assert opp.target_id == "TR-01"
    assert opp.visibility_score > 0
