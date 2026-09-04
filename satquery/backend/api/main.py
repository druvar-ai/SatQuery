from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
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
    return {
        "clock": sim_clock.model_dump(),
        "spacecraft_count": len(constellation.get_all_spacecraft()),
        "engine": settings.simulation_engine
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
def setup_demo_scenario():
    from satquery.backend.spacecraft.model import Spacecraft, Sensor
    from satquery.backend.orbit.elements import OrbitalElements
    
    # Clear existing
    constellation.states.clear()
    constellation.spacecraft.clear()
    
    # Add 10 satellites (optical + SAR mix)
    for i in range(10):
        sensor_type = "optical" if i % 2 == 0 else "sar"
        sensor_id = f"s{i}-1"
        sc = Spacecraft(
            spacecraft_id=f"sat-{i}",
            name=f"Sat {i}",
            spacecraft_type="observation",
            celestial_body_id="earth",
            sensors=[Sensor(sensor_id=sensor_id, sensor_type=sensor_type, field_of_view_deg=15.0)]
        )
        elements = OrbitalElements(
            semi_major_axis_km=7000.0 + (i*50),
            eccentricity=0.001,
            inclination_deg=98.0,
            raan_deg=i*36.0,
            arg_periapsis_deg=0.0,
            true_anomaly_deg=i*36.0,
            epoch=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        )
        constellation.add_spacecraft(sc, elements)
        
    return {"status": "success", "message": "Demo scenario initialized with 10 spacecraft."}

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
