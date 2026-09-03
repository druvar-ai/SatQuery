import subprocess
import os
import sys
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class GMATRunner:
    """Executes the GMAT binary against a generated script."""
    
    @staticmethod
    def is_wsl() -> bool:
        if sys.platform == 'linux':
            try:
                with open('/proc/version', 'r') as f:
                    if 'microsoft' in f.read().lower():
                        return True
            except:
                pass
        return False

    @staticmethod
    def to_windows_path(path_str: str) -> str:
        if not GMATRunner.is_wsl():
            return os.path.abspath(path_str)
        try:
            result = subprocess.run(
                ['wslpath', '-w', os.path.abspath(path_str)], 
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.warning(f"wslpath failed: {e}")
            return os.path.abspath(path_str)

    @staticmethod
    def get_gmat_bin() -> Optional[str]:
        # Check environment variable
        env_path = os.environ.get("GMAT_BIN")
        if env_path and os.path.exists(env_path):
            bin_path = env_path
        else:
            # Try common paths if not specified
            common_paths = [
                "E:/GameDev/GMAT/bin/GMAT.exe",
                "E:/GameDev/GMAT/bin/GmatConsole.exe",
                "C:/GMAT/bin/GMAT.exe",
                "C:/Program Files/GMAT/bin/GMAT.exe",
                "/usr/local/bin/GMAT",
                "/opt/GMAT/bin/GMAT"
            ]
            bin_path = None
            for p in common_paths:
                if os.path.exists(p):
                    bin_path = p
                    break
                    
        if not bin_path:
            return None
            
        # Optional: Swap to GmatConsole for better headless behavior
        if bin_path.lower().endswith("gmat.exe"):
            console_path = os.path.join(os.path.dirname(bin_path), "GmatConsole.exe")
            if os.path.exists(console_path):
                bin_path = console_path
                
        return bin_path
        
    @staticmethod
    def is_available() -> bool:
        return GMATRunner.get_gmat_bin() is not None
        
    @staticmethod
    def run_script(script_path: str, timeout_seconds: int = 60) -> Tuple[bool, str, str, str]:
        """
        Runs the GMAT script. 
        Returns (success, stdout, stderr, executed_command).
        """
        bin_path = GMATRunner.get_gmat_bin()
        if not bin_path:
            return False, "", "GMAT executable not found.", ""
            
        win_script_path = GMATRunner.to_windows_path(script_path)
        
        # Determine invocation syntax
        if bin_path.lower().endswith("gmatconsole.exe"):
            cmd = [bin_path, "-r", win_script_path, "-x"]
        else:
            cmd = [bin_path, "--run", win_script_path, "--minimize", "--exit"]
            
        cmd_str = " ".join(cmd)
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout_seconds
            )
            
            if result.returncode != 0:
                msg = f"GMAT execution failed with code {result.returncode}"
                logger.error(msg)
                return False, result.stdout, result.stderr, cmd_str
                
            return True, result.stdout, result.stderr, cmd_str
            
        except subprocess.TimeoutExpired as e:
            msg = f"GMAT execution timed out after {timeout_seconds}s"
            logger.error(msg)
            return False, str(e.stdout) if e.stdout else "", str(e.stderr) if e.stderr else msg, cmd_str
        except Exception as e:
            logger.error(f"GMAT execution error: {e}")
            return False, "", str(e), cmd_str
