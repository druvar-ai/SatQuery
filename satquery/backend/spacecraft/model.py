from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from satquery.backend.sensors.model import Sensor

class Spacecraft(BaseModel):
    spacecraft_id: str
    name: str
    mission_id: Optional[str] = None
    celestial_body_id: str
    spacecraft_type: str
    sensors: List[Sensor] = []
    operational_status: str = "active"
    
    # Placeholders for future phases
    fuel_capacity_kg: Optional[float] = None
    current_fuel_kg: Optional[float] = None
    power_capacity_w: Optional[float] = None
    current_power_w: Optional[float] = None
    communication_status: str = "nominal"
    health_status: str = "nominal"

class SpacecraftState(BaseModel):
    spacecraft_id: str
    timestamp: datetime
    celestial_body_id: str
    position_km: List[float] = [0.0, 0.0, 0.0]  # [x, y, z] in body-centered frame
    velocity_km_s: List[float] = [0.0, 0.0, 0.0]  # [vx, vy, vz]
    altitude_km: float = 0.0
    orbital_elements: Optional[Dict[str, Any]] = None
    visibility_status: str = "unknown"
    sensor_state: str = "idle"
    simulation_source: str = "ANALYTICAL"
