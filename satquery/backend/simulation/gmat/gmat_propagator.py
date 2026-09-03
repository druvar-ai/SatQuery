import os
import uuid
import numpy as np
from typing import Tuple
from datetime import datetime
import logging

from satquery.backend.orbit.propagator import OrbitPropagator
from satquery.backend.orbit.elements import OrbitalElements
from satquery.backend.celestial.body import CelestialBody

from .gmat_script_generator import GMATScriptGenerator
from .gmat_runner import GMATRunner
from .gmat_parser import GMATParser

logger = logging.getLogger(__name__)

class GMATPropagator(OrbitPropagator):
    def __init__(self, temp_dir: str = "data/gmat_temp"):
        self.temp_dir = os.path.abspath(temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def propagate(self, elements: OrbitalElements, target_time: datetime, body: CelestialBody) -> Tuple[np.ndarray, np.ndarray, float]:
        if not GMATRunner.is_available():
            raise RuntimeError("GMAT execution failed: executable not found.")
            
        # 1. Prepare temporary files
        run_id = uuid.uuid4().hex[:8]
        script_path = os.path.join(self.temp_dir, f"prop_{run_id}.script")
        report_path = os.path.join(self.temp_dir, f"report_{run_id}.txt")
        
        # 2. Generate Script
        script_content = GMATScriptGenerator.generate_script(
            elements=elements,
            target_time=target_time,
            body=body,
            output_report_path=report_path
        )
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # 3. Run GMAT
        success = GMATRunner.run_script(script_path)
        if not success:
            raise RuntimeError("GMAT execution failed.")
            
        # 4. Parse output
        result = GMATParser.parse_report(report_path)
        
        # Clean up (optional, but good practice to avoid polluting disk)
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
            if os.path.exists(report_path):
                os.remove(report_path)
        except Exception:
            pass
            
        if result is None:
            raise RuntimeError("Failed to parse GMAT report output.")
            
        pos, vel = result
        
        # 5. Calculate altitude
        r = np.linalg.norm(pos)
        altitude = float(r - body.radius_km)
        
        return pos, vel, altitude
