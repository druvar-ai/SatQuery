import json
import os
from datetime import datetime

class BlenderExporter:
    @staticmethod
    def export_state(filepath: str, state_data: dict):
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert datetime objects to string
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
            
        with open(filepath, 'w') as f:
            json.dump(state_data, f, default=default_serializer, indent=2)
