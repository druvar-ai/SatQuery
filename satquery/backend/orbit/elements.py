from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Maneuver(BaseModel):
    name: str = Field(description="Name/identifier of the maneuver")
    time_from_epoch_sec: float = Field(description="Time from epoch in seconds to execute the burn")
    dv_v: float = Field(default=0.0, description="Delta-V in Velocity direction (km/s)")
    dv_n: float = Field(default=0.0, description="Delta-V in Normal direction (km/s)")
    dv_b: float = Field(default=0.0, description="Delta-V in Bi-normal direction (km/s)")

class OrbitalElements(BaseModel):
    semi_major_axis_km: float = Field(description="Semi-major axis (a)")
    eccentricity: float = Field(description="Eccentricity (e)")
    inclination_deg: float = Field(description="Inclination (i) in degrees")
    raan_deg: float = Field(description="Right Ascension of the Ascending Node (RAAN) in degrees")
    arg_periapsis_deg: float = Field(description="Argument of Periapsis (omega) in degrees")
    true_anomaly_deg: float = Field(description="True Anomaly (nu) in degrees")
    epoch: datetime = Field(description="Time at which these elements are valid")
    maneuvers: List[Maneuver] = Field(default_factory=list, description="List of scheduled maneuvers")
