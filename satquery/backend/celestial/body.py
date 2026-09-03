from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class CelestialBody(ABC):
    id: str
    name: str
    type: str
    radius_km: float
    mu_km3_s2: float  # Gravitational parameter
    
class Earth(CelestialBody):
    id = "earth"
    name = "Earth"
    type = "planet"
    radius_km = 6378.137
    mu_km3_s2 = 398600.4418
    
    def __init__(self):
        super().__init__(id=self.id, name=self.name, type=self.type, radius_km=self.radius_km, mu_km3_s2=self.mu_km3_s2)

class Moon(CelestialBody):
    id = "moon"
    name = "Moon"
    type = "moon"
    radius_km = 1737.4
    mu_km3_s2 = 4902.800066
    
    def __init__(self):
        super().__init__(id=self.id, name=self.name, type=self.type, radius_km=self.radius_km, mu_km3_s2=self.mu_km3_s2)

class Mars(CelestialBody):
    id = "mars"
    name = "Mars"
    type = "planet"
    radius_km = 3389.5
    mu_km3_s2 = 42828.375214
    
    def __init__(self):
        super().__init__(id=self.id, name=self.name, type=self.type, radius_km=self.radius_km, mu_km3_s2=self.mu_km3_s2)

BODY_REGISTRY = {
    "earth": Earth(),
    "moon": Moon(),
    "mars": Mars()
}

def get_body(body_id: str) -> CelestialBody:
    body = BODY_REGISTRY.get(body_id.lower())
    if not body:
        raise ValueError(f"Unknown celestial body: {body_id}")
    return body
