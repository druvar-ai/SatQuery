from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
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
        self.trajectory_cache: Dict[str, tuple[list[datetime], np.ndarray, np.ndarray, np.ndarray]] = {}
        # We will re-initialize this per propagation call or via API
        self.propagator = get_propagator(settings.simulation_engine)
        
    def set_engine(self, engine_type: str):
        self.propagator = get_propagator(engine_type)
        self.trajectory_cache.clear()
        
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
                # 1. Check if we need to generate a new trajectory batch
                cached = self.trajectory_cache.get(sc_id)
                needs_propagation = True
                
                if cached:
                    times, pos_arr, vel_arr, alt_arr = cached
                    if len(times) > 0 and times[0] <= current_time <= times[-1]:
                        needs_propagation = False
                
                if needs_propagation:
                    # Propagate for a 24-hour window from current_time to avoid repeated calls
                    end_time = current_time + timedelta(hours=24)
                    times, pos_arr, vel_arr, alt_arr = self.propagator.propagate_trajectory(
                        elements=elements,
                        start_time=current_time,
                        end_time=end_time,
                        timestep_seconds=60.0,
                        body=body
                    )
                    self.trajectory_cache[sc_id] = (times, pos_arr, vel_arr, alt_arr)
                    
                # 2. Extract state at exactly current_time via interpolation
                times, pos_arr, vel_arr, alt_arr = self.trajectory_cache.get(sc_id, ([], np.array([]), np.array([]), np.array([])))
                
                if not times:
                    continue
                    
                t0 = times[0]
                t_target_sec = (current_time - t0).total_seconds()
                t_arr_sec = np.array([(t - t0).total_seconds() for t in times])
                
                pos = np.zeros(3)
                vel = np.zeros(3)
                for i in range(3):
                    pos[i] = np.interp(t_target_sec, t_arr_sec, pos_arr[:, i])
                    vel[i] = np.interp(t_target_sec, t_arr_sec, vel_arr[:, i])
                alt = float(np.interp(t_target_sec, t_arr_sec, alt_arr))
                
                # Determine source dynamically based on the actual class returned
                source_label = "GMAT" if self.propagator.__class__.__name__ == "GMATPropagator" else "ANALYTICAL"
                
                state = SpacecraftState(
                    spacecraft_id=sc_id,
                    timestamp=current_time,
                    celestial_body_id=sc.celestial_body_id,
                    position_km=pos.tolist(),
                    velocity_km_s=vel.tolist(),
                    altitude_km=alt,
                    orbital_elements=elements.model_dump(),
                    visibility_status="unknown",
                    sensor_state=sc.sensors[0].sensor_type if sc.sensors else "idle",
                    simulation_source=source_label
                )
                self.states[sc_id] = state
            except Exception as e:
                logger.error(f"Error propagating spacecraft {sc_id}: {e}")
