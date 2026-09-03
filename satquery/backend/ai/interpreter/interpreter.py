import re
from typing import Optional
from satquery.backend.ai.schemas import QueryIntent

class QueryInterpreter:
    """Deterministic rule-based NLP parser for MVP."""
    
    @staticmethod
    def parse(query: str, obs_id: Optional[str] = None, obs_id_2: Optional[str] = None) -> QueryIntent:
        q_lower = query.lower()
        
        task = "SCENE_DESCRIPTION"
        modality = None
        
        # Simple intent matching
        if "change" in q_lower or "difference" in q_lower:
            task = "CHANGE_DETECTION"
        elif "compare" in q_lower and "sar" in q_lower and "optical" in q_lower:
            task = "MULTIMODAL_COMPARISON"
        elif "object" in q_lower or "identify" in q_lower:
            task = "OBJECT_IDENTIFICATION"
        elif "vegetation" in q_lower or "water" in q_lower or "urban" in q_lower:
            task = "LAND_COVER_CLASSIFICATION"
            
        # Modality detection
        if "sar" in q_lower or "radar" in q_lower:
            modality = "sar"
        elif "optical" in q_lower or "visual" in q_lower:
            modality = "optical"
        elif "multispectral" in q_lower:
            modality = "multispectral"
            
        return QueryIntent(
            raw_query=query,
            task=task,
            modality=modality,
            observation_id=obs_id,
            second_observation_id=obs_id_2
        )
