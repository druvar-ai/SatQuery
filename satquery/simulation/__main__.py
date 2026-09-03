import argparse
import sys
import uuid
import datetime
import random
import logging

from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.simulation.clock import SimulationClock
from satquery.backend.spacecraft.model import Spacecraft
from satquery.backend.sensors.model import Sensor
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.celestial.body import get_body
from satquery.simulation.blender import BlenderExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("satquery.cli")

def generate_random_orbit(body_id: str, altitude_km: float) -> OrbitalElements:
    body = get_body(body_id)
    return OrbitalElements(
        semi_major_axis_km=body.radius_km + altitude_km,
        eccentricity=random.uniform(0.001, 0.05),
        inclination_deg=random.uniform(0, 180),
        raan_deg=random.uniform(0, 360),
        arg_periapsis_deg=random.uniform(0, 360),
        true_anomaly_deg=random.uniform(0, 360),
        epoch=datetime.datetime.now(datetime.timezone.utc)
    )

def run_scenario(scenario: str, satellites: int):
    logger.info(f"Starting scenario: {scenario} with {satellites} satellites")
    
    if scenario == "earth_observation":
        body_id = "earth"
        alt = 500.0
    elif scenario == "moon_observation":
        body_id = "moon"
        alt = 100.0
    elif scenario == "mars_observation":
        body_id = "mars"
        alt = 300.0
    else:
        logger.error(f"Unknown scenario: {scenario}")
        sys.exit(1)
        
    constellation = ConstellationManager()
    
    for i in range(satellites):
        sc_id = f"SAT-{i:03d}"
        sensor = Sensor(sensor_id=f"SENS-{i}", sensor_type=random.choice(["optical", "sar", "multispectral"]), field_of_view_deg=15.0)
        sc = Spacecraft(
            spacecraft_id=sc_id,
            name=f"Observer-{i}",
            celestial_body_id=body_id,
            spacecraft_type="orbiter",
            sensors=[sensor]
        )
        elements = generate_random_orbit(body_id, alt)
        constellation.add_spacecraft(sc, elements)
        
    clock = SimulationClock(
        current_time=datetime.datetime.now(datetime.timezone.utc),
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2),
        timestep_seconds=60.0
    )
    
    clock.play()
    
    logger.info("Propagating initial state...")
    constellation.propagate_all(clock.current_time)
    
    state_export = {
        "timestamp": clock.current_time,
        "body": body_id,
        "spacecraft": [s.model_dump() for s in constellation.states.values()],
        "targets": [],
        "observations": []
    }
    
    export_path = f"data/export_{scenario}.json"
    BlenderExporter.export_state(export_path, state_export)
    logger.info(f"Exported simulation state to {export_path}")
    logger.info("Scenario run complete.")

def main():
    parser = argparse.ArgumentParser(description="SatQuery Simulation CLI")
    parser.add_argument("action", choices=["run"], help="Action to perform")
    parser.add_argument("--scenario", type=str, required=True, help="Scenario name (earth_observation, moon_observation, mars_observation)")
    parser.add_argument("--satellites", type=int, default=20, help="Number of satellites to simulate")
    
    args = parser.parse_args()
    
    if args.action == "run":
        run_scenario(args.scenario, args.satellites)

if __name__ == "__main__":
    main()
