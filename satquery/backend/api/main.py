from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import datetime
import uuid

from satquery.backend.database.database import engine, Base, get_db
from satquery.backend.database import models
from satquery.backend.celestial.body import BODY_REGISTRY
from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.simulation.clock import SimulationClock
from satquery.configs.settings import settings
from satquery.backend.models.registry import registry
from satquery.backend.ai.interpreter.interpreter import QueryInterpreter
from satquery.backend.ai.router.router import ModelRouter
from satquery.backend.ai.pipelines.optical_sar import OpticalAnalysisPipeline, SARAnalysisPipeline
from satquery.backend.ai.pipelines.advanced import ChangeDetectionPipeline, MultimodalAnalysisPipeline
from satquery.backend.ai.schemas import QueryIntent
from satquery.backend.observation.planner import ObservationPlanner
from satquery.backend.mission.model import Mission, TargetRegion
from satquery.backend.data.providers.local import LocalSampleProvider
from satquery.simulation.blender import BlenderExporter
from satquery.backend.models.optical.adapters import SatMAEAdapter, SatlasPretrainAdapter
from satquery.backend.models.sar.adapters import SARMAEAdapter, SARHubAdapter
from satquery.backend.models.vlm.adapters import VLMAdapter
from satquery.backend.simulation.scenarios import get_scenario, list_scenarios, SCENARIO_REGISTRY
from satquery.backend.simulation.events import MissionEvent

# Register models
registry.register(SatMAEAdapter())
registry.register(SatlasPretrainAdapter())
registry.register(SARMAEAdapter())
registry.register(SARHubAdapter())
registry.register(VLMAdapter())

# Initialize AI Components
model_router = ModelRouter(registry)
optical_pipeline = OpticalAnalysisPipeline(registry)
sar_pipeline = SARAnalysisPipeline(registry)
change_pipeline = ChangeDetectionPipeline(registry)
multimodal_pipeline = MultimodalAnalysisPipeline(registry)

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SatQuery API", description="Multi-Spacecraft, Multi-Modal AI Mission Intelligence Platform")

# Global state for simulation
constellation = ConstellationManager()
sim_clock = SimulationClock(
    current_time=datetime.datetime.now(datetime.timezone.utc),
    start_time=datetime.datetime.now(datetime.timezone.utc),
    end_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
)
active_scenario_id: Optional[str] = None  # Track which scenario is loaded

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/api/bodies")
def get_bodies():
    return [{"id": b.id, "name": b.name, "type": b.type} for b in BODY_REGISTRY.values()]

@app.get("/api/spacecraft")
def get_spacecraft():
    return [sc.model_dump() for sc in constellation.get_all_spacecraft()]

@app.get("/api/spacecraft/{sc_id}/state")
def get_spacecraft_state(sc_id: str):
    state = constellation.get_state(sc_id)
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state.model_dump()

@app.get("/api/simulation/state")
def get_simulation_state():
    scenario_info = None
    if active_scenario_id and active_scenario_id in SCENARIO_REGISTRY:
        s = SCENARIO_REGISTRY[active_scenario_id]
        scenario_info = {
            "scenario_id": s.scenario_id,
            "name": s.name,
            "celestial_body_id": s.celestial_body_id,
            "description": s.description,
        }
    return {
        "clock": sim_clock.model_dump(),
        "spacecraft_count": len(constellation.get_all_spacecraft()),
        "engine": settings.simulation_engine,
        "active_scenario": scenario_info,
    }

@app.post("/api/simulation/start")
def start_simulation():
    sim_clock.play()
    return {"status": "started", "time": sim_clock.current_time}

@app.post("/api/simulation/stop")
def stop_simulation():
    sim_clock.pause()
    return {"status": "stopped", "time": sim_clock.current_time}

@app.post("/api/simulation/reset")
def reset_simulation():
    sim_clock.reset()
    return {"status": "reset", "time": sim_clock.current_time}

# Example placeholder for missions
@app.get("/api/missions")
def get_missions(db: Session = Depends(get_db)):
    missions = db.query(models.DBMission).all()
    return [{"id": m.id, "name": m.name, "status": m.status} for m in missions]

@app.post("/api/mission")
def create_mission(mission_data: dict, db: Session = Depends(get_db)):
    m_id = str(uuid.uuid4())
    db_mission = models.DBMission(
        id=m_id,
        name=mission_data.get("name", "Unnamed Mission"),
        target_body_id=mission_data.get("target_body_id", "earth"),
        start_time=datetime.datetime.now(datetime.timezone.utc),
        end_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
        status="planned"
    )
    db.add(db_mission)
    db.commit()
    return {"status": "created", "mission_id": m_id}

# Step function for running without loop in background for demo purposes
@app.post("/api/simulation/step")
def step_simulation():
    sim_clock.step(force=True)
    constellation.propagate_all(sim_clock.current_time)
    
    # Export for Blender on step
    try:
        state_data = {
            "time": sim_clock.current_time,
            "spacecraft": [sc.model_dump() for sc in constellation.get_all_spacecraft()],
            "states": {sc_id: state.model_dump() for sc_id, state in constellation.states.items()}
        }
        BlenderExporter.export_state("data/blender_export.json", state_data)
    except Exception as e:
        pass # Non-critical for API failure
        
    return {"time": sim_clock.current_time}

@app.post("/api/simulation/run")
def run_simulation(data: dict):
    # E.g. {"engine": "gmat", "duration_seconds": 3600, "step_seconds": 60}
    engine = data.get("engine", "local")
    constellation.set_engine(engine)
    
    # Step the simulation
    # (For demo purposes, we'll just do a single step like the existing endpoint)
    if sim_clock.running:
        sim_clock.step()
        constellation.propagate_all(sim_clock.current_time)
    
    return {"time": sim_clock.current_time}

@app.get("/api/simulation/status")
def get_simulation_status():
    from satquery.backend.simulation.gmat.gmat_runner import GMATRunner
    
    gmat_avail = GMATRunner.is_available()
    active_engine = "gmat" if constellation.propagator.__class__.__name__ == "GMATPropagator" else "analytical"
    
    msg = "GMAT available" if gmat_avail else "GMAT unavailable; using analytical fallback"
    
    return {
        "active_engine": active_engine,
        "gmat_available": gmat_avail,
        "analytical_available": True,
        "gmat_path": GMATRunner.get_gmat_bin(),
        "message": msg
    }

@app.post("/api/demo/setup")
def setup_demo_scenario(data: dict = None):
    """Load a mission scenario from the scenario registry.
    
    Accepts {"scenario_id": "earth_observation"} etc.
    Defaults to earth_observation if no scenario_id provided.
    """
    global active_scenario_id
    
    scenario_id = "earth_observation"
    if data and isinstance(data, dict):
        scenario_id = data.get("scenario_id", "earth_observation")
    
    try:
        scenario = get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Clear existing state
    constellation.states.clear()
    constellation.spacecraft.clear()
    constellation.orbit_elements.clear()
    constellation.trajectory_cache.clear()
    
    # Load spacecraft from scenario
    for cfg in scenario.spacecraft_configs:
        constellation.add_spacecraft(cfg.spacecraft, cfg.elements)
    
    # Reset clock to scenario epoch and duration
    sim_clock.start_time = scenario.epoch
    sim_clock.current_time = scenario.epoch
    sim_clock.end_time = scenario.epoch + datetime.timedelta(hours=scenario.duration_hours)
    sim_clock.running = False
    sim_clock.speed = 1.0
    sim_clock.timestep_seconds = 60.0
    
    active_scenario_id = scenario_id
    
    # Initial propagation so states are available immediately
    constellation.propagate_all(sim_clock.current_time)
    
    return {
        "status": "success",
        "scenario_id": scenario_id,
        "message": f"Loaded scenario '{scenario.name}' with {len(scenario.spacecraft_configs)} spacecraft.",
    }


@app.get("/api/scenarios")
def get_scenarios():
    """List all available mission scenarios."""
    return list_scenarios()


@app.get("/api/scenarios/{scenario_id}")
def get_scenario_detail(scenario_id: str):
    """Get full details of a specific scenario."""
    try:
        scenario = get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "scenario_id": scenario.scenario_id,
        "name": scenario.name,
        "description": scenario.description,
        "celestial_body_id": scenario.celestial_body_id,
        "epoch": scenario.epoch.isoformat(),
        "duration_hours": scenario.duration_hours,
        "spacecraft_count": len(scenario.spacecraft_configs),
        "spacecraft": [cfg.spacecraft.model_dump() for cfg in scenario.spacecraft_configs],
        "events": [e.model_dump() for e in scenario.events],
    }


@app.get("/api/simulation/events")
def get_simulation_events():
    """Get mission events for the active scenario with status relative to current sim time."""
    if not active_scenario_id or active_scenario_id not in SCENARIO_REGISTRY:
        return []
    
    scenario = SCENARIO_REGISTRY[active_scenario_id]
    elapsed_sec = (sim_clock.current_time - scenario.epoch).total_seconds()
    
    return [
        {
            **e.model_dump(),
            "status": e.status(elapsed_sec),
            "status_icon": e.status_icon(elapsed_sec),
        }
        for e in scenario.events
    ]

@app.post("/api/observations/plan")
def plan_observation(target_data: dict):
    mission = Mission(
        mission_id="ui-mission",
        name="UI Mission",
        description="UI Planned Mission",
        target_body_id=target_data.get("body_id", "earth"),
        mission_objective="observation",
        start_time=sim_clock.current_time,
        end_time=sim_clock.current_time + datetime.timedelta(days=1),
        spacecraft_ids=[sc.spacecraft_id for sc in constellation.get_all_spacecraft()]
    )
    target = TargetRegion(
        target_id="ui-target",
        name="UI Target",
        body_id=target_data.get("body_id", "earth"),
        latitude_deg=float(target_data.get("lat", 0.0)),
        longitude_deg=float(target_data.get("lon", 0.0)),
        priority=1
    )
    planner = ObservationPlanner(constellation)
    opportunities = planner.calculate_opportunities(
        mission=mission,
        target=target,
        time_window_start=mission.start_time,
        time_window_end=mission.end_time,
        timestep_seconds=60.0
    )
    return [opp.model_dump() for opp in opportunities]

@app.get("/api/blender/export")
def trigger_blender_export():
    state_data = {
        "time": sim_clock.current_time,
        "spacecraft": [sc.model_dump() for sc in constellation.get_all_spacecraft()],
        "states": {sc_id: state.model_dump() for sc_id, state in constellation.states.items()}
    }
    BlenderExporter.export_state("data/blender_export.json", state_data)
    return {"status": "exported", "file": "data/blender_export.json"}

@app.get("/api/history")
def get_query_history(db: Session = Depends(get_db)):
    history = db.query(models.DBQueryHistory).order_by(models.DBQueryHistory.timestamp.desc()).all()
    return [{
        "id": h.id,
        "timestamp": h.timestamp,
        "query": h.raw_query,
        "task": h.intent_task,
        "pipeline": h.selected_pipeline,
        "model": h.selected_model,
        "answer": h.response_summary,
        "confidence": h.confidence_value
    } for h in history]

@app.post("/api/simulation/speed")
def set_simulation_speed(data: dict):
    speed = float(data.get("speed", 1.0))
    # Base timestep is 1 second, so speed directly maps to seconds per step
    sim_clock.speed = speed
    sim_clock.timestep_seconds = 1.0
    return {"status": "speed_updated", "speed": sim_clock.speed}

@app.get("/api/spacecraft/{sc_id}/trajectory")
def get_spacecraft_trajectory(sc_id: str):
    """Returns the full cached trajectory for drawing 3D orbit lines."""
    try:
        times, pos, vel, alt = constellation.trajectory_cache[sc_id]
        # times are datetime objects (not UNIX timestamps)
        return {
            "spacecraft_id": sc_id,
            "times_iso": [t.isoformat() if isinstance(t, datetime.datetime) else str(t) for t in times],
            "position_km": pos.tolist(),
            "velocity_km_s": vel.tolist(),
            "altitude_km": alt.tolist(),
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Trajectory not found in cache")

# --- PART 2 AI ENDPOINTS ---

@app.get("/api/data/providers")
def get_providers():
    return [
        {"name": "local-sample", "status": "AVAILABLE"},
        {"name": "sentinel-2", "status": "UNAVAILABLE (MVP fallback)"},
        {"name": "sentinel-1", "status": "UNAVAILABLE (MVP fallback)"}
    ]

@app.get("/api/models")
def get_models():
    return registry.get_all_models()

@app.post("/api/analysis/query")
def analyze_query(query: dict, db: Session = Depends(get_db)):
    raw = query.get("query", "")
    obs_id = query.get("observation_id")
    
    intent = QueryInterpreter.parse(raw, obs_id)
    pipeline_name, model_id, trace = model_router.route(intent, intent.modality or "optical")
    
    # Use LocalSampleProvider to acquire actual synthetic imagery
    provider = LocalSampleProvider(data_dir="data/test_samples")
    meta = provider.search(0.0, 0.0, datetime.datetime.now(datetime.timezone.utc), datetime.datetime.now(datetime.timezone.utc), modality=intent.modality or "optical")[0]
    acquired_image = provider.acquire(meta, obs_id or "obs-unknown")
    
    if pipeline_name == "optical_analysis":
        result = optical_pipeline.execute(intent, [acquired_image], trace)
    elif pipeline_name == "sar_analysis":
        result = sar_pipeline.execute(intent, [acquired_image], trace)
    elif pipeline_name == "change_detection":
        # Fake 2nd image for change detection baseline
        meta2 = provider.search(0.0, 0.0, datetime.datetime.now(datetime.timezone.utc), datetime.datetime.now(datetime.timezone.utc), modality=intent.modality or "optical")[0]
        acquired_image2 = provider.acquire(meta2, obs_id or "obs-unknown")
        result = change_pipeline.execute(intent, [acquired_image, acquired_image2], trace)
    else:
        result = multimodal_pipeline.execute(intent, [acquired_image], trace)
        
    # Store history
    db_history = models.DBQueryHistory(
        id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        raw_query=intent.raw_query,
        intent_task=intent.task,
        observation_ids=result.observation_ids,
        selected_pipeline=result.pipeline,
        selected_model=result.model,
        response_summary=result.answer,
        confidence_value=result.confidence.value,
        routing_trace=result.routing_trace
    )
    db.add(db_history)
    db.commit()
    
    return result.model_dump()
