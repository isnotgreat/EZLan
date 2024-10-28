from ezlan.utils.logger import Logger
import requests
import os
import subprocess
import platform
import shutil
from pathlib import Path
import time
import winreg

class SystemInstaller:
    def __init__(self):
        self.logger = Logger("SystemInstaller")
        self.resources_dir = Path(__file__).parent.parent / "resources"
        self.tap_driver_path = self.resources_dir / "tap-windows.exe"
        self.tap_adapter_key = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"

    def install_tap_driver(self):
        """Install TAP driver if not already installed"""
        if self._is_tap_driver_installed():
            return True
            
        try:
            if not self.tap_driver_path.exists():
                raise RuntimeError("TAP driver installer not found")
                
            # Run the TAP driver installer
            result = subprocess.run([
                str(self.tap_driver_path)
            ], check=True, capture_output=True, text=True)
            
            time.sleep(5)
            
            if not self._is_tap_driver_installed():
                raise RuntimeError("TAP driver installation failed")
                
            return True
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install TAP driver: {e.stderr}")

    def check_and_setup(self):
        """Check and setup required system components"""
        try:
            if platform.system().lower() == 'windows':
                if not self._is_tap_driver_installed():
                    self.logger.info("TAP driver not found, launching installer...")
                    
                    if not self.tap_driver_path.exists():
                        raise RuntimeError("TAP driver installer not found in resources folder")
                    
                    self.logger.info("Please complete the TAP driver installation wizard...")
                    process = subprocess.run([str(self.tap_driver_path)], shell=True)
                    
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        if self._is_tap_driver_installed():
                            self.logger.info("TAP driver installation completed successfully")
                            return True
                        time.sleep(10)
                        self.logger.info("Waiting for TAP driver installation to complete...")
                    
                    raise RuntimeError("TAP driver installation timed out - please try again")
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            raise RuntimeError(f"Failed to setup required components: {e}")

    def _is_tap_driver_installed(self):
        """Check if TAP driver is installed using Windows registry"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.tap_adapter_key, 0, winreg.KEY_READ) as key:
                # Enumerate all network adapters
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                component_id = winreg.QueryValueEx(subkey, "ComponentId")[0]
                                if component_id == "tap0901":
                                    self.logger.info("Found TAP driver in registry")
                                    return True
                            except WindowsError:
                                pass
                        index += 1
                    except WindowsError:
                        break
            return False
        except Exception as e:
            self.logger.error(f"Error checking registry: {e}")
            return False
