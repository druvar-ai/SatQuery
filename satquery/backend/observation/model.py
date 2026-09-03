from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SpacecraftObservation(BaseModel):
    observation_id: str
    mission_id: Optional[str] = None
    spacecraft_id: str
    celestial_body_id: str
    target_region_id: str
    timestamp: datetime
    spacecraft_position_km: List[float]
    spacecraft_velocity_km_s: List[float]
    altitude_km: float
    sensor_id: str
    sensor_type: str
    viewing_geometry: Dict[str, Any] = Field(default_factory=dict)
    visibility: float
    observation_status: str = "planned"
    image_reference: Optional[str] = "Image pending"
    modality: str
    simulation_source: str = "Local Propagator"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ObservationOpportunity(BaseModel):
    spacecraft_id: str
    target_id: str
    body_id: str
    sensor_id: str
    start_time: datetime
    peak_time: datetime
    end_time: datetime
    visibility_score: float
    geometry_score: float
    sensor_score: float
    overall_score: float
