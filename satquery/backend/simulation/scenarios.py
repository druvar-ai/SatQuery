"""
Scenario registry for SatQuery mission simulation.

Each scenario defines a complete mission configuration:
spacecraft, orbital elements, celestial body, epoch, duration,
and mission events. Scenarios are loaded by the API and drive
both the simulation backend and the frontend visualization.

Built-in scenarios:
  1. Earth Observation Constellation — 6 SSO spacecraft
  2. Hohmann Transfer Demo — LEO-to-GEO with 2 reference spacecraft
  3. Lunar Reconnaissance — 3 spacecraft around the Moon
  4. Mars Survey — 3 spacecraft around Mars
"""

import datetime
import math
from typing import List, Dict, Tuple
from pydantic import BaseModel, Field

from satquery.backend.spacecraft.model import Spacecraft
from satquery.backend.sensors.model import Sensor
from satquery.backend.orbit.elements import OrbitalElements, Maneuver
from satquery.backend.simulation.events import MissionEvent


class SpacecraftConfig(BaseModel):
    """A spacecraft + its orbital elements bundled for scenario setup."""
    spacecraft: Spacecraft
    elements: OrbitalElements


class MissionScenario(BaseModel):
    """A complete, self-contained mission scenario."""
    scenario_id: str
    name: str
    description: str
    celestial_body_id: str
    epoch: datetime.datetime
    duration_hours: float = 24.0
    spacecraft_configs: List[SpacecraftConfig] = []
    events: List[MissionEvent] = []


# ─────────────────────────────────────────────────────────────
# Built-in scenario definitions
# ─────────────────────────────────────────────────────────────

_EPOCH = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def _earth_observation_scenario() -> MissionScenario:
    """6 spacecraft in sun-synchronous-like orbits with mixed sensors."""
    configs = []
    sensor_types = ["optical", "sar", "multispectral", "optical", "sar", "optical"]
    names = [
        "EO-1 Sentinel", "EO-2 Radar", "EO-3 Spectrum",
        "EO-4 Imager", "EO-5 SAR-B", "EO-6 Optical-C",
    ]

    for i in range(6):
        sc = Spacecraft(
            spacecraft_id=f"eo-{i}",
            name=names[i],
            spacecraft_type="observation",
            celestial_body_id="earth",
            sensors=[Sensor(
                sensor_id=f"eo-s{i}",
                sensor_type=sensor_types[i],
                field_of_view_deg=15.0,
                resolution_m=10.0 if sensor_types[i] == "optical" else 25.0,
            )],
        )
        elements = OrbitalElements(
            semi_major_axis_km=6878.0 + i * 30,  # ~500 km altitude spread
            eccentricity=0.001,
            inclination_deg=97.4,  # Sun-synchronous
            raan_deg=i * 60.0,    # Spread across RAAN
            arg_periapsis_deg=0.0,
            true_anomaly_deg=i * 60.0,  # Spread in orbit
            epoch=_EPOCH,
        )
        configs.append(SpacecraftConfig(spacecraft=sc, elements=elements))

    events = [
        MissionEvent(event_id="eo-e0", name="Mission Epoch", event_type="epoch",
                     time_from_epoch_sec=0, description="Constellation deployment complete", icon="🚀"),
        MissionEvent(event_id="eo-e1", name="First Light — EO-1", event_type="observation",
                     time_from_epoch_sec=2700, spacecraft_id="eo-0",
                     description="First optical image acquired", icon="📸"),
        MissionEvent(event_id="eo-e2", name="SAR Pass — EO-2", event_type="observation",
                     time_from_epoch_sec=5400, spacecraft_id="eo-1",
                     description="First SAR acquisition over target zone", icon="📡"),
        MissionEvent(event_id="eo-e3", name="Nominal Operations", event_type="phase_change",
                     time_from_epoch_sec=7200,
                     description="All spacecraft in nominal observation mode", icon="✅"),
        MissionEvent(event_id="eo-e4", name="Global Coverage Pass", event_type="milestone",
                     time_from_epoch_sec=21600,
                     description="Full equatorial coverage achieved (6h mark)", icon="🌍"),
    ]

    return MissionScenario(
        scenario_id="earth_observation",
        name="Earth Observation Constellation",
        description="Six spacecraft in sun-synchronous orbits performing multi-sensor Earth observation.",
        celestial_body_id="earth",
        epoch=_EPOCH,
        duration_hours=24.0,
        spacecraft_configs=configs,
        events=events,
    )


def _hohmann_transfer_scenario() -> MissionScenario:
    """Hohmann transfer from LEO (~622 km) to GEO (35,786 km).

    Three spacecraft for visual context:
      - sat-h0: The transfer spacecraft (with 2 ΔV maneuvers)
      - sat-h1: Reference — parking orbit (stays in LEO)
      - sat-h2: Reference — target orbit (already in GEO)
    """
    # Transfer spacecraft
    # Parking orbit: a = 7000 km (alt ≈ 622 km)
    # Target orbit:  a = 42164 km (GEO)
    # Transfer semi-major axis: (7000 + 42164) / 2 = 24582 km
    # Transfer period: T = 2π√(a³/μ) ≈ 5.26 hours → half = ~18900s
    # We use the existing maneuver times that match the GMAT script generator

    transfer_sc = Spacecraft(
        spacecraft_id="sat-h0",
        name="Transfer Vehicle",
        spacecraft_type="transfer",
        celestial_body_id="earth",
        mission_id="hohmann",
        sensors=[Sensor(sensor_id="h0-s", sensor_type="optical", field_of_view_deg=10.0)],
    )
    transfer_elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=0.0,  # Equatorial for clean Hohmann visualization
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=_EPOCH,
        maneuvers=[
            Maneuver(name="Transfer_Injection", time_from_epoch_sec=3600.0, dv_v=2.603),
            Maneuver(name="Circularization", time_from_epoch_sec=22683.0, dv_v=1.390),
        ],
    )

    # Reference: parking orbit (no maneuvers)
    parking_sc = Spacecraft(
        spacecraft_id="sat-h1",
        name="Parking Orbit Ref",
        spacecraft_type="reference",
        celestial_body_id="earth",
        sensors=[Sensor(sensor_id="h1-s", sensor_type="optical", field_of_view_deg=10.0)],
    )
    parking_elements = OrbitalElements(
        semi_major_axis_km=7000.0,
        eccentricity=0.001,
        inclination_deg=0.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=120.0,  # Offset so it's visible separately
        epoch=_EPOCH,
    )

    # Reference: target GEO orbit
    geo_sc = Spacecraft(
        spacecraft_id="sat-h2",
        name="GEO Target Ref",
        spacecraft_type="reference",
        celestial_body_id="earth",
        sensors=[Sensor(sensor_id="h2-s", sensor_type="optical", field_of_view_deg=10.0)],
    )
    geo_elements = OrbitalElements(
        semi_major_axis_km=42164.0,
        eccentricity=0.001,
        inclination_deg=0.0,
        raan_deg=0.0,
        arg_periapsis_deg=0.0,
        true_anomaly_deg=0.0,
        epoch=_EPOCH,
    )

    events = [
        MissionEvent(event_id="h-e0", name="Mission Epoch", event_type="epoch",
                     time_from_epoch_sec=0,
                     description="Transfer vehicle in parking orbit (7,000 km)", icon="🚀"),
        MissionEvent(event_id="h-e1", name="Parking Orbit Phase", event_type="phase_change",
                     time_from_epoch_sec=0, spacecraft_id="sat-h0",
                     description="Coasting in LEO parking orbit", icon="🛰️"),
        MissionEvent(event_id="h-e2", name="ΔV₁ — Transfer Injection", event_type="maneuver",
                     time_from_epoch_sec=3600.0, spacecraft_id="sat-h0",
                     description="Prograde burn: +2.603 km/s → enter transfer ellipse", icon="🔥"),
        MissionEvent(event_id="h-e3", name="Transfer Coast", event_type="phase_change",
                     time_from_epoch_sec=3660.0, spacecraft_id="sat-h0",
                     description="Coasting on Hohmann transfer ellipse", icon="🛰️"),
        MissionEvent(event_id="h-e4", name="ΔV₂ — Circularization", event_type="maneuver",
                     time_from_epoch_sec=22683.0, spacecraft_id="sat-h0",
                     description="Prograde burn: +1.390 km/s → circularize at GEO", icon="🔥"),
        MissionEvent(event_id="h-e5", name="GEO Achieved", event_type="milestone",
                     time_from_epoch_sec=22743.0, spacecraft_id="sat-h0",
                     description="Transfer vehicle in geostationary orbit (42,164 km)", icon="✅"),
    ]

    return MissionScenario(
        scenario_id="hohmann_transfer",
        name="Hohmann Transfer — LEO to GEO",
        description="Demonstrates a Hohmann transfer from low Earth orbit (622 km) to geostationary orbit (35,786 km) with two impulsive burns.",
        celestial_body_id="earth",
        epoch=_EPOCH,
        duration_hours=8.0,  # ~8 hours covers the full transfer
        spacecraft_configs=[
            SpacecraftConfig(spacecraft=transfer_sc, elements=transfer_elements),
            SpacecraftConfig(spacecraft=parking_sc, elements=parking_elements),
            SpacecraftConfig(spacecraft=geo_sc, elements=geo_elements),
        ],
        events=events,
    )


def _lunar_reconnaissance_scenario() -> MissionScenario:
    """3 spacecraft in low lunar orbit for surface mapping."""
    configs = []
    names = ["Luna-1 Mapper", "Luna-2 Radar", "Luna-3 Spectral"]
    sensor_types = ["optical", "sar", "multispectral"]

    for i in range(3):
        sc = Spacecraft(
            spacecraft_id=f"luna-{i}",
            name=names[i],
            spacecraft_type="observation",
            celestial_body_id="moon",
            sensors=[Sensor(
                sensor_id=f"luna-s{i}",
                sensor_type=sensor_types[i],
                field_of_view_deg=12.0,
            )],
        )
        elements = OrbitalElements(
            semi_major_axis_km=1837.4 + i * 20,  # ~100 km altitude
            eccentricity=0.005,
            inclination_deg=90.0,  # Polar for full coverage
            raan_deg=i * 60.0,
            arg_periapsis_deg=0.0,
            true_anomaly_deg=i * 120.0,
            epoch=_EPOCH,
        )
        configs.append(SpacecraftConfig(spacecraft=sc, elements=elements))

    events = [
        MissionEvent(event_id="lu-e0", name="Mission Epoch", event_type="epoch",
                     time_from_epoch_sec=0, description="Lunar constellation deployed", icon="🚀"),
        MissionEvent(event_id="lu-e1", name="First Lunar Pass — Luna-1", event_type="observation",
                     time_from_epoch_sec=1800, spacecraft_id="luna-0",
                     description="First optical pass over near side", icon="📸"),
        MissionEvent(event_id="lu-e2", name="Far Side Mapping", event_type="phase_change",
                     time_from_epoch_sec=3600,
                     description="Spacecraft entering far-side coverage", icon="🌑"),
        MissionEvent(event_id="lu-e3", name="Full Surface Coverage", event_type="milestone",
                     time_from_epoch_sec=14400,
                     description="Complete polar-orbit surface mapping cycle", icon="✅"),
    ]

    return MissionScenario(
        scenario_id="lunar_reconnaissance",
        name="Lunar Reconnaissance",
        description="Three spacecraft in polar lunar orbits for surface mapping and reconnaissance.",
        celestial_body_id="moon",
        epoch=_EPOCH,
        duration_hours=12.0,
        spacecraft_configs=configs,
        events=events,
    )


def _mars_survey_scenario() -> MissionScenario:
    """3 spacecraft in Mars orbit for surface survey."""
    configs = []
    names = ["Ares-1 Imager", "Ares-2 Radar", "Ares-3 Multi"]
    sensor_types = ["optical", "sar", "multispectral"]

    for i in range(3):
        sc = Spacecraft(
            spacecraft_id=f"ares-{i}",
            name=names[i],
            spacecraft_type="observation",
            celestial_body_id="mars",
            sensors=[Sensor(
                sensor_id=f"ares-s{i}",
                sensor_type=sensor_types[i],
                field_of_view_deg=14.0,
            )],
        )
        elements = OrbitalElements(
            semi_major_axis_km=3689.5 + i * 25,  # ~300 km altitude
            eccentricity=0.01,
            inclination_deg=93.0,  # Near-polar sun-sync analog
            raan_deg=i * 60.0,
            arg_periapsis_deg=0.0,
            true_anomaly_deg=i * 120.0,
            epoch=_EPOCH,
        )
        configs.append(SpacecraftConfig(spacecraft=sc, elements=elements))

    events = [
        MissionEvent(event_id="ma-e0", name="Mission Epoch", event_type="epoch",
                     time_from_epoch_sec=0, description="Mars constellation deployed", icon="🚀"),
        MissionEvent(event_id="ma-e1", name="First Mars Image — Ares-1", event_type="observation",
                     time_from_epoch_sec=3000, spacecraft_id="ares-0",
                     description="First optical acquisition over Valles Marineris region", icon="📸"),
        MissionEvent(event_id="ma-e2", name="SAR Pass — Ares-2", event_type="observation",
                     time_from_epoch_sec=6000, spacecraft_id="ares-1",
                     description="First SAR pass over polar ice cap", icon="📡"),
        MissionEvent(event_id="ma-e3", name="Nominal Operations", event_type="phase_change",
                     time_from_epoch_sec=10800,
                     description="All spacecraft in nominal survey mode", icon="✅"),
    ]

    return MissionScenario(
        scenario_id="mars_survey",
        name="Mars Survey",
        description="Three spacecraft in near-polar Mars orbits for surface survey and mapping.",
        celestial_body_id="mars",
        epoch=_EPOCH,
        duration_hours=24.0,
        spacecraft_configs=configs,
        events=events,
    )


# ─────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────

SCENARIO_REGISTRY: Dict[str, MissionScenario] = {}


def _register_builtins():
    """Populate the registry with built-in scenarios."""
    for factory in [
        _earth_observation_scenario,
        _hohmann_transfer_scenario,
        _lunar_reconnaissance_scenario,
        _mars_survey_scenario,
    ]:
        scenario = factory()
        SCENARIO_REGISTRY[scenario.scenario_id] = scenario


_register_builtins()


def get_scenario(scenario_id: str) -> MissionScenario:
    """Retrieve a scenario by ID."""
    scenario = SCENARIO_REGISTRY.get(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIO_REGISTRY.keys())}")
    return scenario


def list_scenarios() -> List[Dict]:
    """Return summary metadata for all registered scenarios."""
    return [
        {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "description": s.description,
            "celestial_body_id": s.celestial_body_id,
            "spacecraft_count": len(s.spacecraft_configs),
            "duration_hours": s.duration_hours,
        }
        for s in SCENARIO_REGISTRY.values()
    ]
