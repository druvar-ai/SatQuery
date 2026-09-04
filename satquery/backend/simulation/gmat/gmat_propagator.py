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
        script_path = os.path.abspath(os.path.join(self.temp_dir, f"prop_{run_id}.script"))
        report_path = os.path.abspath(os.path.join(self.temp_dir, f"report_{run_id}.txt"))
        
        # We need to give GMAT the Windows equivalent paths if we're on WSL
        win_report_path = GMATRunner.to_windows_path(report_path)
        
        # 2. Generate Script
        script_content = GMATScriptGenerator.generate_script(
            elements=elements,
            target_time=target_time,
            body=body,
            output_report_path=win_report_path
        )
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # 3. Run GMAT
        success, stdout, stderr, cmd_str = GMATRunner.run_script(script_path)
        
        if not success:
            err_msg = (
                f"GMAT execution failed.\n"
                f"Command: {cmd_str}\n"
                f"Script retained at: {script_path}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)
            
        # 4. Parse output
        result = GMATParser.parse_report(report_path)
        
        if result is None:
            err_msg = (
                f"Failed to parse GMAT report output at {report_path}.\n"
                f"Script retained at: {script_path}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)
            
        # Clean up on success
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
            if os.path.exists(report_path):
                os.remove(report_path)
        except Exception:
            pass
            
        pos, vel = result
        
        # 5. Calculate altitude
        r = np.linalg.norm(pos)
        altitude = float(r - body.radius_km)
        
        return pos, vel, altitude

    def propagate_trajectory(self, elements: OrbitalElements, start_time: datetime, end_time: datetime, timestep_seconds: float, body: CelestialBody) -> Tuple[list[datetime], np.ndarray, np.ndarray, np.ndarray]:
        if not GMATRunner.is_available():
            raise RuntimeError("GMAT execution failed: executable not found.")
            
        from datetime import timedelta
        run_id = uuid.uuid4().hex[:8]
        script_path = os.path.abspath(os.path.join(self.temp_dir, f"prop_batch_{run_id}.script"))
        report_path = os.path.abspath(os.path.join(self.temp_dir, f"report_batch_{run_id}.txt"))
        
        win_report_path = GMATRunner.to_windows_path(report_path)
        
        # We propagate to end_time to ensure we capture the entire requested window
        script_content = GMATScriptGenerator.generate_script(
            elements=elements,
            target_time=end_time,
            body=body,
            output_report_path=win_report_path,
            step_size=timestep_seconds
        )
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        success, stdout, stderr, cmd_str = GMATRunner.run_script(script_path, timeout_seconds=120)
        
        if not success:
            err_msg = (
                f"GMAT batch execution failed.\n"
                f"Command: {cmd_str}\n"
                f"Script retained at: {script_path}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)
            
        result = GMATParser.parse_report_batch(report_path)
        
        if result is None:
            err_msg = (
                f"Failed to parse GMAT batch report output at {report_path}.\n"
                f"Script retained at: {script_path}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )
            logger.error(err_msg)
            raise RuntimeError(err_msg)
            
        # Clean up on success
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
            if os.path.exists(report_path):
                os.remove(report_path)
        except Exception:
            pass
            
        gmat_times, gmat_pos, gmat_vel = result
        
        # We now have adaptive steps from epoch to end_time.
        # We must interpolate them exactly onto [start_time, end_time] with timestep_seconds.
        target_times = []
        curr = start_time
        while curr <= end_time:
            target_times.append(curr)
            curr += timedelta(seconds=timestep_seconds)
            
        if not target_times:
            return [], np.array([]), np.array([]), np.array([])
            
        # Convert all datetimes to seconds relative to the first GMAT point
        t0 = gmat_times[0]
        gmat_secs = np.array([(t - t0).total_seconds() for t in gmat_times])
        target_secs = np.array([(t - t0).total_seconds() for t in target_times])
        
        interp_pos = np.zeros((len(target_times), 3))
        interp_vel = np.zeros((len(target_times), 3))
        
        for i in range(3):
            interp_pos[:, i] = np.interp(target_secs, gmat_secs, gmat_pos[:, i])
            interp_vel[:, i] = np.interp(target_secs, gmat_secs, gmat_vel[:, i])
            
        # Vectorized altitude
        r_norms = np.linalg.norm(interp_pos, axis=1)
        interp_alt = r_norms - body.radius_km
        
        return target_times, interp_pos, interp_vel, interp_alt
