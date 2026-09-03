import os
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class GMATParser:
    """Parses GMAT ReportFile outputs to extract terminal state."""
    
    @staticmethod
    def parse_report(report_path: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Parses the final line of a GMAT ReportFile.
        Expected format: UTCGregorian X Y Z VX VY VZ
        Returns:
            position (numpy array): [x, y, z] in km
            velocity (numpy array): [vx, vy, vz] in km/s
        """
        if not os.path.exists(report_path):
            logger.error(f"GMAT report file not found: {report_path}")
            return None
            
        try:
            with open(report_path, 'r') as f:
                lines = f.readlines()
                
            # Filter out empty lines and header (which usually contains % or column names)
            data_lines = [l.strip() for l in lines if l.strip() and not l.startswith('%') and not l.startswith('Sat.UTCGregorian')]
            
            if not data_lines:
                logger.error("GMAT report file contains no data rows.")
                return None
                
            # The last line should be the target epoch (or the end of propagation)
            final_line = data_lines[-1]
            
            # Since UTCGregorian has spaces (e.g. '01 Jan 2000 12:00:00.000'), 
            # parsing blindly by space is tricky. 
            # We know X Y Z VX VY VZ are the last 6 tokens.
            tokens = final_line.split()
            if len(tokens) < 6:
                logger.error("GMAT report line contains insufficient tokens.")
                return None
                
            x, y, z = float(tokens[-6]), float(tokens[-5]), float(tokens[-4])
            vx, vy, vz = float(tokens[-3]), float(tokens[-2]), float(tokens[-1])
            
            return np.array([x, y, z]), np.array([vx, vy, vz])
            
        except Exception as e:
            logger.error(f"Error parsing GMAT report: {e}")
            return None
