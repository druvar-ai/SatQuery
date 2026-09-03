import numpy as np
import math
from typing import List, Optional
from datetime import datetime, timedelta
from satquery.backend.mission.model import Mission, TargetRegion
from satquery.backend.spacecraft.model import Spacecraft, SpacecraftState
from satquery.backend.observation.model import ObservationOpportunity
from satquery.backend.simulation.constellation import ConstellationManager
from satquery.backend.celestial.body import get_body

class ObservationPlanner:
    def __init__(self, constellation: ConstellationManager):
        self.constellation = constellation

    def calculate_opportunities(
        self,
        mission: Mission,
        target: TargetRegion,
        time_window_start: datetime,
        time_window_end: datetime,
        timestep_seconds: float = 60.0
    ) -> List[ObservationOpportunity]:
        opportunities = []
        body = get_body(target.body_id)
        
        # Target cartesian coordinates (simplified spherical assumption)
        lat = math.radians(target.latitude_deg)
        lon = math.radians(target.longitude_deg)
        r = body.radius_km
        
        tx = r * math.cos(lat) * math.cos(lon)
        ty = r * math.cos(lat) * math.sin(lon)
        tz = r * math.sin(lat)
        target_pos = np.array([tx, ty, tz])
        
        # For each spacecraft in the mission
        for sc_id in mission.spacecraft_ids:
            sc = self.constellation.get_spacecraft(sc_id)
            if not sc or not sc.sensors:
                continue
                
            sensor = sc.sensors[0] # Pick first sensor for MVP
            
            # Simple simulation loop to find visibility windows
            current_time = time_window_start
            
            in_view = False
            window_start = None
            peak_time = None
            min_dist = float('inf')
            
            # NOTE: For MVP we just step through time.
            # In a real system, we'd use root-finding or analytical methods for access times.
            while current_time <= time_window_end:
                # Propagate orbit (in an optimized version, we'd propagate just one SC at a time)
                # But here we assume state is either available or we can compute it on the fly.
                elements = self.constellation.orbit_elements.get(sc_id)
                if not elements:
                    break
                    
                pos, vel, alt = self.constellation.propagator.propagate(elements, current_time, body)
                
                # Simple line of sight (LOS) and elevation angle check
                dist = np.linalg.norm(pos - target_pos)
                
                # Check horizon/elevation
                # Target normal vector
                target_normal = target_pos / np.linalg.norm(target_pos)
                sc_vector = pos - target_pos
                sc_dir = sc_vector / dist
                
                elevation_angle = math.degrees(math.asin(np.dot(sc_dir, target_normal)))
                
                # Assuming visible if elevation > 10 degrees
                is_visible = elevation_angle > 10.0
                
                if is_visible:
                    if not in_view:
                        in_view = True
                        window_start = current_time
                    
                    if dist < min_dist:
                        min_dist = dist
                        peak_time = current_time
                else:
                    if in_view:
                        # End of window
                        in_view = False
                        
                        # Score calculation
                        visibility_score = min(1.0, 90.0 / (dist / 10.0 + 1.0)) # Fake formula
                        geometry_score = 0.9 # Placeholder
                        sensor_score = 0.95 # Placeholder
                        overall_score = (visibility_score * 0.5) + (geometry_score * 0.25) + (sensor_score * 0.25)
                        
                        opp = ObservationOpportunity(
                            spacecraft_id=sc_id,
                            target_id=target.target_id,
                            body_id=target.body_id,
                            sensor_id=sensor.sensor_id,
                            start_time=window_start,
                            peak_time=peak_time,
                            end_time=current_time,
                            visibility_score=visibility_score,
                            geometry_score=geometry_score,
                            sensor_score=sensor_score,
                            overall_score=overall_score
                        )
                        opportunities.append(opp)
                        
                        # Reset
                        min_dist = float('inf')
                        
                current_time += timedelta(seconds=timestep_seconds)
                
        # Sort by overall score
        opportunities.sort(key=lambda x: x.overall_score, reverse=True)
        return opportunities
