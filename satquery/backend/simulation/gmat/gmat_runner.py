import subprocess
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GMATRunner:
    """Executes the GMAT binary against a generated script."""
    
    @staticmethod
    def get_gmat_bin() -> Optional[str]:
        # Check environment variable
        env_path = os.environ.get("GMAT_BIN")
        if env_path and os.path.exists(env_path):
            return env_path
            
        # Try common paths if not specified
        common_paths = [
            "C:/GMAT/bin/GMAT.exe",
            "C:/Program Files/GMAT/bin/GMAT.exe",
            "/usr/local/bin/GMAT",
            "/opt/GMAT/bin/GMAT"
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p
        return None
        
    @staticmethod
    def is_available() -> bool:
        return GMATRunner.get_gmat_bin() is not None
        
    @staticmethod
    def run_script(script_path: str, timeout_seconds: int = 60) -> bool:
        bin_path = GMATRunner.get_gmat_bin()
        if not bin_path:
            logger.error("GMAT executable not found.")
            return False
            
        try:
            # GMAT typically takes --run --exit arguments or similar for headless,
            # but standard invocation is: GMAT.exe --run "script.script" --minimize --exit
            cmd = [bin_path, "--run", script_path, "--minimize", "--exit"]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout_seconds
            )
            
            if result.returncode != 0:
                logger.error(f"GMAT execution failed with code {result.returncode}: {result.stderr}")
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("GMAT execution timed out.")
            return False
        except Exception as e:
            logger.error(f"GMAT execution error: {e}")
            return False
