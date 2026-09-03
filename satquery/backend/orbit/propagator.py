import math
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Tuple
from satquery.backend.celestial.body import CelestialBody
from satquery.backend.orbit.elements import OrbitalElements

class OrbitPropagator(ABC):
    @abstractmethod
    def propagate(self, elements: OrbitalElements, target_time: datetime, body: CelestialBody) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Propagate orbit to target time.
        Returns:
            position (numpy array): [x, y, z] in km
            velocity (numpy array): [vx, vy, vz] in km/s
            altitude (float): in km
        """
        pass

class AnalyticalPropagator(OrbitPropagator):
    def propagate(self, elements: OrbitalElements, target_time: datetime, body: CelestialBody) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Simple Keplerian analytical propagator.
        Assumes 2-body problem.
        """
        # Convert to radians
        inc = math.radians(elements.inclination_deg)
        raan = math.radians(elements.raan_deg)
        arg_p = math.radians(elements.arg_periapsis_deg)
        nu_0 = math.radians(elements.true_anomaly_deg)
        
        a = elements.semi_major_axis_km
        e = elements.eccentricity
        mu = body.mu_km3_s2
        
        # Mean motion
        n = math.sqrt(mu / (a**3))
        
        # Time difference in seconds
        dt = (target_time - elements.epoch).total_seconds()
        
        # Initial eccentric anomaly (E_0)
        E_0 = 2 * math.atan(math.sqrt((1 - e) / (1 + e)) * math.tan(nu_0 / 2))
        
        # Initial mean anomaly (M_0)
        M_0 = E_0 - e * math.sin(E_0)
        
        # Mean anomaly at target time
        M = M_0 + n * dt
        
        # Solve Kepler's equation for Eccentric Anomaly (E)
        E = M
        for _ in range(10): # Simple Newton-Raphson
            E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
            
        # True anomaly at target time
        nu = 2 * math.atan(math.sqrt((1 + e) / (1 - e)) * math.tan(E / 2))
        
        # Distance (r)
        r = a * (1 - e * math.cos(E))
        
        # Position in perifocal frame
        p_p = r * math.cos(nu)
        p_q = r * math.sin(nu)
        
        # Velocity in perifocal frame
        p_dot = math.sqrt(mu * a) / r
        v_p = -p_dot * math.sin(E)
        v_q = p_dot * math.sqrt(1 - e**2) * math.cos(E)
        
        # Transformation matrix (Perifocal to Body-Centered Inertial)
        # Using RAAN, inclination, argument of periapsis
        R3_W = np.array([
            [math.cos(-raan), -math.sin(-raan), 0],
            [math.sin(-raan), math.cos(-raan), 0],
            [0, 0, 1]
        ])
        R1_i = np.array([
            [1, 0, 0],
            [0, math.cos(-inc), -math.sin(-inc)],
            [0, math.sin(-inc), math.cos(-inc)]
        ])
        R3_w = np.array([
            [math.cos(-arg_p), -math.sin(-arg_p), 0],
            [math.sin(-arg_p), math.cos(-arg_p), 0],
            [0, 0, 1]
        ])
        
        Q = R3_W @ R1_i @ R3_w
        
        pos_perifocal = np.array([p_p, p_q, 0])
        vel_perifocal = np.array([v_p, v_q, 0])
        
        pos_inertial = Q @ pos_perifocal
        vel_inertial = Q @ vel_perifocal
        
        altitude = r - body.radius_km
        
        return pos_inertial, vel_inertial, altitude

def get_propagator(engine_type: str = "local") -> OrbitPropagator:
    if engine_type == "local" or engine_type == "analytical":
        return AnalyticalPropagator()
    elif engine_type == "gmat":
        from satquery.backend.simulation.gmat.gmat_propagator import GMATPropagator
        from satquery.backend.simulation.gmat.gmat_runner import GMATRunner
        if GMATRunner.is_available():
            return GMATPropagator()
        else:
            # Fallback to analytical gracefully
            return AnalyticalPropagator()
    else:
        raise ValueError(f"Unknown propagation engine: {engine_type}")
