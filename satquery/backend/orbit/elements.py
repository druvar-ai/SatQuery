from pydantic import BaseModel, Field
from datetime import datetime

class OrbitalElements(BaseModel):
    semi_major_axis_km: float = Field(description="Semi-major axis (a)")
    eccentricity: float = Field(description="Eccentricity (e)")
    inclination_deg: float = Field(description="Inclination (i) in degrees")
    raan_deg: float = Field(description="Right Ascension of the Ascending Node (RAAN) in degrees")
    arg_periapsis_deg: float = Field(description="Argument of Periapsis (omega) in degrees")
    true_anomaly_deg: float = Field(description="True Anomaly (nu) in degrees")
    epoch: datetime = Field(description="Time at which these elements are valid")
