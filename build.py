import sys
import ctypes
import traceback
import asyncio
import qasync
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from ezlan.gui.main_window import MainWindow
from ezlan.network.discovery import DiscoveryService
from ezlan.network.interface_manager import InterfaceManager
from ezlan.network.tunnel import TunnelService
from ezlan.utils.installer import SystemInstaller
from ezlan.utils.logger import Logger
import PyInstaller.__main__

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    """Restart the program with admin rights."""
    try:
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1
        )
        if ret <= 32:  # Error codes from ShellExecuteW
            raise RuntimeError(f"Failed to elevate privileges (error code: {ret})")
        return True
    except Exception as e:
        print(f"Failed to get admin rights: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller."""
    try:
        # Define the build options
        PyInstaller.__main__.run([
            'ezlan/main.py',  # Path to your main application file
            '--name=EZLan',  # Name of the executable
            '--onefile',  # Create a single executable
            '--icon=ezlan/resources/icon.ico',  # Path to the application icon
            '--add-data=ezlan/resources;resources',  # Include additional data files
            '--clean',  # Clean up temporary files
            '--log-level=WARN',  # Set log level
            '--hidden-import=scipy.special._cdflib',  # Include the hidden import
            '--hidden-import=h2',
            '--hidden-import=zstandard',
            '--hidden-import=brotli',
        ])
        print("Build completed successfully!")
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

def main():
    if not is_admin():
        if elevate():
            return
        sys.exit(1)

    build_executable()

if __name__ == "__main__":
    main()

