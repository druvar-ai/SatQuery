from pydantic import BaseModel, Field
from typing import Optional, List

class Sensor(BaseModel):
    sensor_id: str
    sensor_type: str = Field(description="optical, multispectral, sar, etc.")
    field_of_view_deg: float
    resolution_m: Optional[float] = None
    swath_width_km: Optional[float] = None
    operational_status: str = "active"
