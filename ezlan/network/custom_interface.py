from PyQt6.QtCore import QObject, pyqtSignal
import subprocess
import time
from ..utils.logger import Logger

class CustomNetworkInterface(QObject):
    interface_created = pyqtSignal(str)    # interface_name
    interface_error = pyqtSignal(str)      # error_message
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("CustomNetworkInterface")
        self.interface_name = "EZLan Virtual Network"
        self.is_windows = True  # Assuming Windows for this implementation
        
    def create_interface(self) -> bool:
        try:
            if self.is_windows:
                self.logger.info("Creating Hyper-V virtual switch 'EZLan'")
                # Create Hyper-V virtual switch using PowerShell
                subprocess.run([
                    "powershell", "-Command",
                    "New-VMSwitch -Name 'EZLan' -SwitchType Internal"
                ], check=True, capture_output=True)
                
                self.logger.info("Renaming the virtual adapter to 'EZLan Virtual Network'")
                # Rename the virtual adapter
                subprocess.run([
                    "netsh", "interface", "set", "interface",
                    "name='vEthernet (EZLan)'", "newname='EZLan Virtual Network'",
                    "admin=enabled"
                ], check=True, capture_output=True)
                
                self.interface_created.emit(self.interface_name)
                self.logger.info(f"Created virtual interface: {self.interface_name}")
                return True
            else:
                # Implement Linux or other OS-specific interface creation if needed
                self.logger.error("Unsupported operating system for interface creation.")
                self.interface_error.emit("Unsupported operating system for interface creation.")
                return False
                
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode().strip()
            self.logger.error(f"Interface creation failed: {error_message}")
            self.interface_error.emit(error_message)
            return False
        except Exception as e:
            self.logger.error(f"Interface creation failed: {e}")
            self.interface_error.emit(str(e))
            return False