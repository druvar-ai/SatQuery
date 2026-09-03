from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ObservationImage(BaseModel):
    image_id: str
    observation_id: str
    source_provider: str = Field(description="e.g., sentinel-1, sentinel-2, local-sample")
    source_product_id: Optional[str] = None
    modality: str = Field(description="e.g., optical, multispectral, sar")
    bands: List[str] = []
    image_reference: str = Field(description="File path or URL to the image array")
    dimensions: List[int] = Field(description="[width, height, channels]")
    acquisition_time: datetime
    simulated: bool = False
    
    # Metadata bridges to the simulation
    celestial_body_id: str
    spacecraft_id: Optional[str] = None
    sensor_id: Optional[str] = None
    target_region_id: Optional[str] = None
    
    geographic_metadata: Dict[str, Any] = Field(default_factory=dict)
    preprocessing_metadata: Dict[str, Any] = Field(default_factory=dict)
