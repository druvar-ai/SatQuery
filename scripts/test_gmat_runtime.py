import os
import sys
import subprocess
import shutil
import tempfile
import pathlib

def is_wsl():
    if sys.platform == 'linux':
        try:
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return True
        except:
            pass
    return False

def to_windows_path(path_str):
    """Converts a WSL path to a Windows path using wslpath."""
    if not is_wsl():
        return os.path.abspath(path_str)
    
    try:
        result = subprocess.run(['wslpath', '-w', os.path.abspath(path_str)], 
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Warning: wslpath failed: {e}")
        return os.path.abspath(path_str)

def get_gmat_executable():
    bin_path = os.environ.get("GMAT_BIN", "/mnt/e/GameDev/GMAT/bin/GMAT.exe")
    
    # Optional: Swap to GmatConsole for better headless behavior
    if bin_path.lower().endswith("gmat.exe"):
        console_path = os.path.join(os.path.dirname(bin_path), "GmatConsole.exe")
        if os.path.exists(console_path):
            bin_path = console_path
            
    return bin_path

def main():
    print("=== GMAT RUNTIME DIAGNOSTIC ===")
    print(f"Platform: {sys.platform}")
    print(f"Is WSL: {is_wsl()}")
    
    gmat_bin = get_gmat_executable()
    print(f"Configured GMAT_BIN: {gmat_bin}")
    
    if not os.path.exists(gmat_bin):
        print(f"ERROR: Executable not found at {gmat_bin}")
        sys.exit(1)
        
    if is_wsl():
        win_bin = to_windows_path(gmat_bin)
        print(f"Windows path for executable: {win_bin}")
    
    temp_dir = tempfile.mkdtemp(prefix="gmat_test_")
    print(f"Working directory: {temp_dir}")
    
    script_path = os.path.join(temp_dir, "test.script")
    report_path = os.path.join(temp_dir, "report.txt")
    
    win_report_path = to_windows_path(report_path)
    
    # Generate minimal script
    # We must use forward slashes or escaped backslashes for GMAT string literals
    gmat_report_str = win_report_path.replace("\\", "/")
    
    script = f"""
Create Spacecraft Sat;
GMAT Sat.DateFormat = UTCGregorian;
GMAT Sat.Epoch = '01 Jan 2026 00:00:00.000';
Create ForceModel DefaultProp_ForceModel;
GMAT DefaultProp_ForceModel.CentralBody = Earth;
GMAT DefaultProp_ForceModel.PointMasses = {{Earth}};
GMAT DefaultProp_ForceModel.Drag = None;
GMAT DefaultProp_ForceModel.SRP = Off;
Create Propagator DefaultProp;
GMAT DefaultProp.FM = DefaultProp_ForceModel;
Create ReportFile ReportFile1;
GMAT ReportFile1.Filename = '{gmat_report_str}';
GMAT ReportFile1.Add = {{Sat.UTCGregorian, Sat.EarthMJ2000Eq.X, Sat.EarthMJ2000Eq.Y, Sat.EarthMJ2000Eq.Z, Sat.EarthMJ2000Eq.VX, Sat.EarthMJ2000Eq.VY, Sat.EarthMJ2000Eq.VZ}};
GMAT ReportFile1.WriteReport = true;
BeginMissionSequence;
Propagate DefaultProp(Sat) {{Sat.ElapsedSecs = 3600.0}};
"""

    with open(script_path, 'w') as f:
        f.write(script)
        
    win_script_path = to_windows_path(script_path)
    print(f"Generated script (Windows path): {win_script_path}")
    print(f"Expected report (Windows path): {win_report_path}")
    
    cmd = [gmat_bin, "--run", win_script_path, "--minimize", "--exit"]
    if gmat_bin.lower().endswith("gmatconsole.exe"):
        cmd = [gmat_bin, "-r", win_script_path, "-x"]
        
    print(f"Executing: {' '.join(cmd)}")
    
    try:
        # Run GMAT
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(f"Return Code: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        
        if os.path.exists(report_path):
            print("\nReport File Created!")
            with open(report_path, 'r') as f:
                print(f.read())
        else:
            print("\nERROR: Report File NOT Created!")
            
    except Exception as e:
        print(f"Execution failed: {e}")

if __name__ == "__main__":
    main()
