from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from satquery.backend.database.database import Base
from datetime import datetime

class DBMission(Base):
    __tablename__ = "missions"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    target_body_id = Column(String)
    mission_objective = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String)
    
    spacecraft_ids = Column(JSON) # List of strings
    
class DBTargetRegion(Base):
    __tablename__ = "target_regions"
    
    id = Column(String, primary_key=True, index=True)
    mission_id = Column(String, ForeignKey("missions.id"))
    body_id = Column(String)
    name = Column(String)
    latitude_deg = Column(Float)
    longitude_deg = Column(Float)

class DBSpacecraft(Base):
    __tablename__ = "spacecraft"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    celestial_body_id = Column(String)
    spacecraft_type = Column(String)
    operational_status = Column(String)
    sensors = Column(JSON) # List of serialized Sensor dicts

class DBObservation(Base):
    __tablename__ = "observations"
    
    id = Column(String, primary_key=True, index=True)
    mission_id = Column(String, ForeignKey("missions.id"))
    spacecraft_id = Column(String, ForeignKey("spacecraft.id"))
    celestial_body_id = Column(String)
    target_region_id = Column(String)
    timestamp = Column(DateTime)
    sensor_id = Column(String)
    sensor_type = Column(String)
    visibility_score = Column(Float)
    status = Column(String)
    image_reference = Column(String)

class DBQueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime)
    raw_query = Column(String)
    intent_task = Column(String)
    observation_ids = Column(JSON) # List of strings
    selected_pipeline = Column(String)
    selected_model = Column(String)
    response_summary = Column(String)
    confidence_value = Column(Float)
    routing_trace = Column(JSON)
