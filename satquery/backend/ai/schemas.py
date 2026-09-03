from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class QueryIntent(BaseModel):
    raw_query: str
    task: str = Field(description="e.g., CHANGE_DETECTION, SCENE_DESCRIPTION, OBJECT_IDENTIFICATION")
    modality: Optional[str] = None
    observation_id: Optional[str] = None
    second_observation_id: Optional[str] = None
    target_region: Optional[str] = None
    date_range: Optional[List[str]] = None
    requested_output: Optional[str] = None
    confidence_requirement: float = 0.5

class Confidence(BaseModel):
    value: float
    type: str = Field(description="e.g., heuristic_score, model_score, system_score")
    calibrated: bool = False

class EvidenceArtifact(BaseModel):
    type: str = Field(description="e.g., bounding_box, change_mask, metadata")
    coordinates: Optional[List[float]] = None
    geometry: Optional[Dict[str, Any]] = None
    image_reference: Optional[str] = None
    explanation: str
    score: Optional[float] = None

class SatQueryResponse(BaseModel):
    query: str
    answer: str
    task: str
    observation_ids: List[str] = []
    modality: str
    pipeline: str
    model: str
    confidence: Confidence
    evidence: List[EvidenceArtifact] = []
    routing_trace: Dict[str, Any] = Field(default_factory=dict)
    source_information: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = []
