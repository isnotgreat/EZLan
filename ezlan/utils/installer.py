from ..utils.logger import Logger
import subprocess
import json

class SystemInstaller:
    def __init__(self):
        self.logger = Logger("SystemInstaller")
    
    def check_hyper_v_enabled(self) -> bool:
        """Check if Hyper-V is enabled using multiple methods."""
        try:
            # Method 1: Check using PowerShell
            ps_result = subprocess.run([
                "powershell", "-Command",
                "(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All).State"
            ], capture_output=True, text=True, check=True)
            
            if "Enabled" in ps_result.stdout:
                self.logger.info("Hyper-V is enabled (PowerShell check).")
                return True
            
            # Method 2: Check Hyper-V service status
            service_result = subprocess.run([
                "powershell", "-Command",
                "Get-Service vmms | Select-Object -ExpandProperty Status"
            ], capture_output=True, text=True, check=True)
            
            if "Running" in service_result.stdout:
                self.logger.info("Hyper-V service is running.")
                return True
            
            self.logger.info(f"Hyper-V status: PowerShell={ps_result.stdout.strip()}, Service={service_result.stdout.strip()}")
            return False
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to check Hyper-V status: {e.stderr.strip()}")
            return False
    
    def get_detailed_hyper_v_status(self) -> dict:
        """Get detailed Hyper-V status information."""
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "$features = @('Microsoft-Hyper-V', 'Microsoft-Hyper-V-Management-PowerShell', " +
                "'Microsoft-Hyper-V-Management-Clients', 'Microsoft-Hyper-V-Services', " +
                "'Microsoft-Hyper-V-Hypervisor'); " +
                "$status = @{}; " +
                "foreach ($feature in $features) { " +
                "    $state = (Get-WindowsOptionalFeature -Online -FeatureName $feature).State; " +
                "    $status[$feature] = $state; " +
                "}; " +
                "ConvertTo-Json $status"
            ], capture_output=True, text=True, check=True)
            
            return json.loads(result.stdout)
            
        except Exception as e:
            self.logger.error(f"Failed to get detailed Hyper-V status: {e}")
            return {}
    
    def enable_hyper_v(self) -> bool:
        """Enable Hyper-V using PowerShell."""
        try:
            self.logger.info("Enabling Hyper-V...")
            subprocess.run([
                "powershell", "-Command",
                "Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All"
            ], check=True, capture_output=True, text=True)
            self.logger.info("Hyper-V enablement command executed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to enable Hyper-V: {e.stderr.strip()}")
            return False
    
    def check_and_setup(self):
        """Check and setup system requirements."""
        if not self.check_hyper_v_enabled():
            # Get detailed status for debugging
            status = self.get_detailed_hyper_v_status()
            self.logger.info(f"Detailed Hyper-V status: {json.dumps(status, indent=2)}")
            
            user_response = input(
                "Hyper-V is not properly enabled. Do you want to enable it now? (y/n): "
            )
            if user_response.lower() == 'y':
                if self.enable_hyper_v():
                    self.logger.info("Hyper-V enabled successfully. A system restart is required.")
                    raise RuntimeError("Hyper-V has been enabled. Please restart your computer and run the application again.")
                else:
                    self.logger.error("Failed to enable Hyper-V.")
                    raise RuntimeError("Failed to enable Hyper-V. Please enable it manually and restart your computer.")
            else:
                raise RuntimeError("Hyper-V is required for this application to run.")
