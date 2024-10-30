from PyQt6.QtCore import QObject, pyqtSignal
import subprocess
from ..utils.logger import Logger
import asyncio

class HyperVInterfaceManager(QObject):
    interface_created = pyqtSignal(str)    # interface_name
    interface_error = pyqtSignal(str)      # error_message

    def __init__(self):
        super().__init__()
        self.logger = Logger("HyperVInterfaceManager")
        self.interface_name = "EZLan Virtual Network"
    
    async def create_interface(self) -> bool:
        try:
            self.logger.info("Creating Hyper-V virtual switch 'EZLan'")
            
            # Create Hyper-V virtual switch using PowerShell with better error handling
            create_cmd = """
            $ErrorActionPreference = 'Stop'
            try {
                Remove-VMSwitch -Name 'EZLan' -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                New-VMSwitch -Name 'EZLan' -SwitchType Internal
                Start-Sleep -Seconds 2
                $adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Hyper-V*' -and $_.Name -like '*EZLan*' }
                if ($adapter) {
                    Disable-NetAdapter -Name $adapter.Name -Confirm:$false
                    Start-Sleep -Seconds 1
                    Enable-NetAdapter -Name $adapter.Name -Confirm:$false
                    Start-Sleep -Seconds 1
                    Rename-NetAdapter -Name $adapter.Name -NewName 'EZLan Virtual Network' -Confirm:$false
                    Write-Output "Success"
                } else {
                    Write-Error "Adapter not found"
                }
            } catch {
                Write-Error "Failed: $_"
                exit 1
            }
            """
            
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", create_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Failed to create/configure interface: {stderr.decode()}")
                
            if "Success" not in stdout.decode():
                raise RuntimeError("Interface creation did not complete successfully")
                
            self.interface_created.emit(self.interface_name)
            self.logger.info(f"Created virtual interface: {self.interface_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Interface creation failed: {e}")
            self.interface_error.emit(str(e))
            return False

    async def cleanup_interface(self) -> bool:
        try:
            cleanup_cmd = """
        $ErrorActionPreference = 'Stop'
        try {
            # Get all Hyper-V virtual switches with name containing 'EZLan'
            $switches = Get-VMSwitch | Where-Object { $_.Name -like '*EZLan*' }
            foreach ($switch in $switches) {
                # Remove the switch
                Remove-VMSwitch -Name $switch.Name -Force
                
                # Find and remove associated network adapters
                $adapters = Get-NetAdapter | Where-Object { 
                    $_.InterfaceDescription -like '*Hyper-V*' -and 
                    ($_.Name -like '*EZLan*' -or $_.Name -eq 'EZLan Virtual Network')
                }
                foreach ($adapter in $adapters) {
                    Remove-NetAdapter -Name $adapter.Name -Confirm:$false -ErrorAction SilentlyContinue
                }
            }
            Write-Output "Success"
        } catch {
            Write-Error "Failed: $_"
            exit 1
        }
        """
        
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", cleanup_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info("Cleaned up virtual interface: EZLan Virtual Network")
                return True
            else:
                self.logger.error(f"Failed to cleanup interface: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup interface: {e}")
            return False
