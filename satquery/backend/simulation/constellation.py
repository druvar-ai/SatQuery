from typing import Dict, List, Optional
from datetime import datetime
from satquery.backend.spacecraft.model import Spacecraft, SpacecraftState
from satquery.backend.celestial.body import get_body
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.orbit.propagator import get_propagator
from satquery.configs.settings import settings
import logging

logger = logging.getLogger("satquery.constellation")

class ConstellationManager:
    def __init__(self):
        self.spacecraft: Dict[str, Spacecraft] = {}
        self.orbit_elements: Dict[str, OrbitalElements] = {}
        self.states: Dict[str, SpacecraftState] = {}
        self.propagator = get_propagator(settings.simulation_engine)
        
    def add_spacecraft(self, sc: Spacecraft, elements: OrbitalElements):
        self.spacecraft[sc.spacecraft_id] = sc
        self.orbit_elements[sc.spacecraft_id] = elements
        logger.info(f"Added spacecraft {sc.spacecraft_id} ({sc.name}) to constellation.")
        
    def get_spacecraft(self, spacecraft_id: str) -> Optional[Spacecraft]:
        return self.spacecraft.get(spacecraft_id)
        
    def get_all_spacecraft(self) -> List[Spacecraft]:
        return list(self.spacecraft.values())
        
    def get_state(self, spacecraft_id: str) -> Optional[SpacecraftState]:
        return self.states.get(spacecraft_id)
        
    def propagate_all(self, current_time: datetime):
        for sc_id, sc in self.spacecraft.items():
            elements = self.orbit_elements[sc_id]
            body = get_body(sc.celestial_body_id)
            
            try:
                pos, vel, alt = self.propagator.propagate(elements, current_time, body)
                
                state = SpacecraftState(
                    spacecraft_id=sc_id,
                    timestamp=current_time,
                    celestial_body_id=sc.celestial_body_id,
                    position_km=pos.tolist(),
                    velocity_km_s=vel.tolist(),
                    altitude_km=alt,
                    orbital_elements=elements.model_dump(),
                    visibility_status="unknown",
                    sensor_state=sc.sensors[0].sensor_type if sc.sensors else "idle"
                )
                self.states[sc_id] = state
            except Exception as e:
                logger.error(f"Error propagating spacecraft {sc_id}: {e}")
