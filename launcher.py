import sys
import os
import ctypes
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox, QApplication

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
            app = QApplication([])
            QMessageBox.critical(None, "Error", f"Error: Could not find main.py at: {main_script}")
            return

        if not is_admin():
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
                app = QApplication([])
                QMessageBox.critical(None, "Error", f"Failed to get admin rights: {e}")
        else:
            try:
                # We're already admin, run main.py directly
                subprocess.run(
                    [sys.executable, str(main_script)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except Exception as e:
                app = QApplication([])
                QMessageBox.critical(None, "Error", f"Error running EZLan: {e}")

    except Exception as e:
        app = QApplication([])
        QMessageBox.critical(None, "Error", f"Launcher error: {e}")

if __name__ == "__main__":
    main() 