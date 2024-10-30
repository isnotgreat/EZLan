from PyQt6.QtCore import QObject, pyqtSignal
import subprocess
import time
from ..utils.logger import Logger

class HyperVInterfaceManager(QObject):
    interface_created = pyqtSignal(str)    # interface_name
    interface_error = pyqtSignal(str)      # error_message

    def __init__(self):
        super().__init__()
        self.logger = Logger("HyperVInterfaceManager")
        self.interface_name = "EZLan Virtual Network"
        self.is_windows = True  # Currently targeting Windows
        
    def create_interface(self) -> bool:
        try:
            if self.is_windows:
                # First check if switch already exists and remove it
                cleanup_cmd = (
                    "$ErrorActionPreference = 'Stop'; "
                    "try { "
                    "    Get-VMSwitch -Name 'EZLan' -ErrorAction SilentlyContinue | "
                    "    Remove-VMSwitch -Force -ErrorAction SilentlyContinue; "
                    "    Write-Output 'Cleanup successful' "
                    "} catch { "
                    "    Write-Output 'No switch to cleanup' "
                    "}"
                )
                subprocess.run(["powershell", "-Command", cleanup_cmd], capture_output=True)
                
                time.sleep(2)  # Wait for cleanup
                
                # Create new switch
                self.logger.info("Creating Hyper-V virtual switch 'EZLan'")
                create_cmd = (
                    "$ErrorActionPreference = 'Stop'; "
                    "try { "
                    "    $switch = New-VMSwitch -Name 'EZLan' -SwitchType Internal; "
                    "    Write-Output 'Switch created successfully'; "
                    "} catch { "
                    "    Write-Error \"Failed to create switch: $($_.Exception.Message)`n$($_.ScriptStackTrace)\"; "
                    "    exit 1; "
                    "}"
                )
                
                result = subprocess.run(
                    ["powershell", "-Command", create_cmd],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to create switch: {result.stderr}")
                
                time.sleep(3)  # Wait for switch creation
                
                # Get the adapter name
                get_adapter_cmd = (
                    "$adapter = Get-NetAdapter | " +
                    "Where-Object { $_.InterfaceDescription -like '*Hyper-V*' } | " +
                    "Sort-Object CreationTime -Descending | " +
                    "Select-Object -First 1; " +
                    "if ($adapter) { " +
                    "    Write-Output $adapter.Name; " +
                    "} else { " +
                    "    Write-Error 'No adapter found'; " +
                    "    exit 1; " +
                    "}"
                )
                
                result = subprocess.run(
                    ["powershell", "-Command", get_adapter_cmd],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to find adapter: {result.stderr}")
                
                current_name = result.stdout.strip()
                if not current_name:
                    raise RuntimeError("Could not find Hyper-V adapter")
                
                self.logger.info(f"Found adapter: {current_name}")
                
                # Enable the adapter first
                enable_cmd = f"Enable-NetAdapter -Name '{current_name}' -Confirm:$false"
                result = subprocess.run(
                    ["powershell", "-Command", enable_cmd],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to enable adapter: {result.stderr}")
                
                time.sleep(1)
                
                # Now rename the adapter
                rename_cmd = f"Rename-NetAdapter -Name '{current_name}' -NewName '{self.interface_name}' -Confirm:$false"
                result = subprocess.run(
                    ["powershell", "-Command", rename_cmd],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to rename adapter: {result.stderr}")
                
                # Verify the adapter exists with new name
                verify_cmd = f"Get-NetAdapter -Name '{self.interface_name}' -ErrorAction SilentlyContinue"
                result = subprocess.run(
                    ["powershell", "-Command", verify_cmd],
                    capture_output=True,
                    text=True
                )
                
                if self.interface_name not in result.stdout:
                    raise RuntimeError("Failed to verify renamed adapter")
                
                self.interface_created.emit(self.interface_name)
                self.logger.info(f"Created virtual interface: {self.interface_name}")
                return True
                
            else:
                self.logger.error("Unsupported operating system for interface creation.")
                self.interface_error.emit("Unsupported operating system for interface creation.")
                return False
                
        except subprocess.CalledProcessError as e:
            error_message = f"Command failed: {e.stderr.decode() if e.stderr else str(e)}"
            self.logger.error(f"Interface creation failed: {error_message}")
            self.interface_error.emit(error_message)
            return False
        except Exception as e:
            self.logger.error(f"Interface creation failed: {e}")
            self.interface_error.emit(str(e))
            return False

    def cleanup_interface(self):
        """Remove the Hyper-V virtual switch."""
        try:
            self.logger.info("Removing Hyper-V virtual switch 'EZLan'")
            subprocess.run(
                ["powershell", "-Command",
                 "Remove-VMSwitch -Name 'EZLan' -Force"],
                check=True,
                capture_output=True
            )
            self.logger.info(f"Cleaned up virtual interface: {self.interface_name}")
            return True
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode().strip() if e.stderr else str(e)
            self.logger.error(f"Failed to cleanup interface: {error_message}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to cleanup interface: {e}")
            return False

