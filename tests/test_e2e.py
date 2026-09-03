import pytest
import datetime
import uuid
import os
import json

from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.simulation.clock import SimulationClock
from satquery.backend.observation.planner import ObservationPlanner
from satquery.backend.mission.model import Mission, TargetRegion
from satquery.backend.spacecraft.model import Spacecraft, Sensor
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.ai.interpreter.interpreter import QueryInterpreter
from satquery.backend.ai.router.router import ModelRouter
from satquery.backend.models.registry import registry
from satquery.backend.ai.pipelines.optical_sar import OpticalAnalysisPipeline
from satquery.backend.data.providers.local import LocalSampleProvider
from satquery.backend.database.models import Base, DBQueryHistory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_end_to_end_integration():
    # 1. Setup in-memory DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # 2. Simulation (10 spacecraft)
    start_t = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    clock = SimulationClock(
        start_time=start_t,
        current_time=start_t,
        end_time=start_t + datetime.timedelta(days=1)
    )
    constellation = ConstellationManager()
    
    for i in range(10):
        sc = Spacecraft(
            spacecraft_id=f"sat-{i}",
            name=f"Sat {i}",
            spacecraft_type="observation",
            celestial_body_id="earth",
            sensors=[Sensor(sensor_id="opt1", sensor_type="optical", field_of_view_deg=10.0)]
        )
        elements = OrbitalElements(
            semi_major_axis_km=7000.0 + (i*10),
            eccentricity=0.001,
            inclination_deg=98.0,
            raan_deg=0.0,
            arg_periapsis_deg=0.0,
            true_anomaly_deg=i * 36.0,
            epoch=start_t
        )
        constellation.add_spacecraft(sc, elements)
    
    constellation.propagate_all(clock.current_time)
    sats = constellation.get_all_spacecraft() # Not get_state() which returns state models, planner calculate_opportunities uses constellation.get_spacecraft(sc_id) internally
    assert len(sats) == 10
    
    # 3. Observation Opportunity
    mission = Mission(
        mission_id="m1",
        name="Test",
        description="Test",
        target_body_id="earth",
        mission_objective="observation",
        start_time=start_t,
        end_time=start_t + datetime.timedelta(days=1),
        spacecraft_ids=[f"sat-{i}" for i in range(10)]
    )
    target = TargetRegion(target_id="t1", name="Test Target", body_id="earth", latitude_deg=0.0, longitude_deg=0.0, priority=1)
    
    planner = ObservationPlanner(constellation)
    # Just mock that we get a window for the test instead of running the math intensive propagation here
    # We only need the obs_id to flow down the chain
    obs_id = str(uuid.uuid4())
    
    # 4. Local Synthetic Image
    provider = LocalSampleProvider(data_dir="data/test_samples")
    meta = provider.search(target.latitude_deg, target.longitude_deg, clock.current_time, clock.current_time)[0]
    image = provider.acquire(meta, obs_id)
    
    assert image.simulated == True
    assert image.preprocessing_metadata["source"] == "SYNTHETIC TEST DATA"
    
    # 5. Query & Interpretation
    query = "Analyze this optical image."
    intent = QueryInterpreter.parse(query, obs_id)
    assert intent.task == "SCENE_DESCRIPTION"
    
    # 6. Routing
    router = ModelRouter(registry)
    pipeline_name, model_id, trace = router.route(intent, image.modality)
    assert pipeline_name == "optical_analysis"
    assert model_id == "baseline_heuristic"
    
    # 7. Pipeline execution
    pipeline = OpticalAnalysisPipeline(registry)
    response = pipeline.execute(intent, [image], trace)
    
    # 8. Verification of Evidence & Confidence
    assert "BASELINE HEURISTIC" in response.answer
    assert response.confidence.type == "heuristic_score"
    assert response.confidence.calibrated == False
    assert len(response.evidence) > 0
    
    # 9. Database History Write
    db_history = DBQueryHistory(
        id=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        raw_query=intent.raw_query,
        intent_task=intent.task,
        observation_ids=response.observation_ids,
        selected_pipeline=response.pipeline,
        selected_model=response.model,
        response_summary=response.answer,
        confidence_value=response.confidence.value,
        routing_trace=response.routing_trace
    )
    db.add(db_history)
    db.commit()
    
    # 10. Database read verification
    saved = db.query(DBQueryHistory).first()
    assert saved.selected_model == "baseline_heuristic"
    assert saved.intent_task == "SCENE_DESCRIPTION"
    assert saved.raw_query == query
