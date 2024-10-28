import sys
import os
import ctypes
import subprocess
import time
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    try:
        script_dir = Path(__file__).parent
        main_script = script_dir / "ezlan" / "main.py"
        
        if not main_script.exists():
            print(f"Error: Could not find main.py at: {main_script}")
            input("Press Enter to exit...")
            return

        if not is_admin():
            print("Requesting administrator privileges...")
            try:
                # Re-run with admin rights
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas",
                    sys.executable,
                    f'"{main_script}"',
                    str(script_dir),
                    1
                )
            except Exception as e:
                print(f"Failed to get admin rights: {e}")
                input("Press Enter to exit...")
        else:
            print("Running EZLan with administrator privileges...")
            try:
                # We're already admin, run main.py directly
                result = subprocess.run(
                    [sys.executable, str(main_script)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"Error running EZLan:\n{result.stderr}")
                    input("Press Enter to exit...")
            except Exception as e:
                print(f"Error running EZLan: {e}")
                input("Press Enter to exit...")

    except Exception as e:
        print(f"Launcher error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 