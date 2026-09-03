from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class TargetRegion(BaseModel):
    target_id: str
    body_id: str
    name: str
    latitude_deg: float
    longitude_deg: float
    geometry: Optional[Any] = None # Polygon/Bounding box placeholder
    mission_objective: Optional[str] = None

class Mission(BaseModel):
    mission_id: str
    name: str
    description: Optional[str] = None
    target_body_id: str
    spacecraft_ids: List[str] = []
    target_regions: List[TargetRegion] = []
    mission_objective: str
    start_time: datetime
    end_time: datetime
    observation_requirements: Optional[str] = None
    mission_status: str = "planned"
