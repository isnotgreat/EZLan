from abc import ABC, abstractmethod
import platform
import subprocess
import netifaces
import os
import time
import winreg
from pathlib import Path
from ..utils.logger import Logger

class VirtualInterfaceManager(ABC):
    @abstractmethod
    def create_interface(self):
        pass

    @abstractmethod
    def configure_interface(self, ip_address):
        pass

    @abstractmethod
    def cleanup(self):
        pass

class WindowsInterfaceManager(VirtualInterfaceManager):
    def __init__(self):
        self.tap_name = "EZLan_TAP"
        self.component_id = "tap0901"
        self.adapter_key = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
        self.logger = Logger("WindowsInterfaceManager")
        self.needs_restart = False

    def _find_tap_adapter(self):
        """Find existing TAP adapter in registry"""
        try:
            adapter_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
            )
            
            for i in range(1000):
                try:
                    key_name = winreg.EnumKey(adapter_key, i)
                    adapter_path = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}\\{key_name}"
                    
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapter_path) as adapter:
                        try:
                            component_id = winreg.QueryValueEx(adapter, "ComponentId")[0]
                            if component_id == self.component_id:
                                return key_name
                        except WindowsError:
                            continue
                except WindowsError:
                    break
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding TAP adapter: {e}")
            return None
            
    def create_interface(self):
        """Create and initialize TAP interface"""
        try:
            # First check if TAP adapter exists
            tap_idx = self._find_tap_adapter()
            
            if tap_idx is None:
                self.logger.info("TAP adapter not found, installing...")
                self._install_tap_driver()
                time.sleep(2)  # Wait for driver installation
                tap_idx = self._find_tap_adapter()
                
                if tap_idx is None:
                    self.needs_restart = True
                    raise RuntimeError(
                        "TAP driver installation requires a system restart. "
                        "Please restart your computer and try again."
                    )
            
            # Get the actual interface name from network adapters
            interface_name = self._get_interface_name(tap_idx)
            if interface_name:
                self.tap_name = interface_name
            
            # Enable the TAP adapter
            self._enable_tap_adapter(tap_idx)
            
            # Verify adapter is present in network interfaces
            if not self._verify_tap_interface():
                # Try restarting the adapter
                self._restart_adapter(tap_idx)
                time.sleep(2)
                
                if not self._verify_tap_interface():
                    raise RuntimeError(
                        "TAP adapter not properly initialized. "
                        "You may need to restart your computer."
                    )
                    
            return self.tap_name
            
        except Exception as e:
            self.logger.error(f"Failed to create TAP interface: {e}")
            raise
            
    def _get_interface_name(self, adapter_idx):
        """Get the actual interface name from network adapters"""
        try:
            adapter_path = f"{self.adapter_key}\\{adapter_idx}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, adapter_path) as key:
                return winreg.QueryValueEx(key, "NetCfgInstanceId")[0]
        except Exception as e:
            self.logger.error(f"Failed to get interface name: {e}")
            return None

    def _enable_tap_adapter(self, adapter_idx):
        """Enable the TAP adapter"""
        try:
            # Get the actual interface name from network adapters
            interface_id = self._get_interface_name(adapter_idx)
            if not interface_id:
                raise RuntimeError("Could not find TAP adapter interface ID")
            
            # First try using netsh with the interface ID
            try:
                subprocess.run(
                    ["netsh", "interface", "set", "interface", interface_id, "admin=enable"],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                # If that fails, try using PowerShell with the interface ID
                try:
                    subprocess.run(
                        ["powershell", "-Command", 
                         f"Enable-NetAdapter -InterfaceAlias '{interface_id}' -Confirm:$false"],
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError:
                    # Last resort: try with the full interface name
                    subprocess.run(
                        ["powershell", "-Command", 
                         f"Get-NetAdapter | Where-Object InterfaceDescription -like '*TAP-Windows*' | Enable-NetAdapter -Confirm:$false"],
                        check=True,
                        capture_output=True
                    )
                    
            self.logger.info(f"Enabled TAP adapter {interface_id}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to enable TAP adapter: {e}")
            if "access is denied" in str(e).lower():
                raise RuntimeError(
                    "Access denied while enabling TAP adapter. "
                    "Please run the application as administrator."
                )
            raise RuntimeError(
                f"Failed to enable TAP adapter. Please ensure you have administrator privileges "
                f"and the TAP adapter is properly installed. Error: {e}"
            )
            
    def _restart_adapter(self, adapter_idx):
        """Restart the TAP adapter"""
        try:
            # Disable and re-enable the adapter
            subprocess.run(
                ["netsh", "interface", "set", "interface", self.tap_name, "admin=disabled"],
                check=True,
                capture_output=True
            )
            time.sleep(1)
            subprocess.run(
                ["netsh", "interface", "set", "interface", self.tap_name, "admin=enabled"],
                check=True,
                capture_output=True
            )
            self.logger.info(f"Restarted TAP adapter {self.tap_name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to restart TAP adapter: {e}")
            raise
            
    def _verify_tap_interface(self):
        """Verify TAP interface is present in network interfaces"""
        try:
            interfaces = netifaces.interfaces()
            return any(self.tap_name in iface for iface in interfaces)
        except Exception as e:
            self.logger.error(f"Error verifying TAP interface: {e}")
            return False
            
    def configure_interface(self, ip_address):
        """Configure TAP interface with IP address"""
        try:
            # Get the actual adapter name first
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-NetAdapter | Where-Object InterfaceDescription -like '*TAP-Windows*' | Select-Object -ExpandProperty Name"],
                capture_output=True,
                check=True
            )
            adapter_name = result.stdout.decode('utf-8').strip()
            if not adapter_name:
                raise RuntimeError("Could not find TAP adapter name")
            
            # First make sure the adapter is enabled
            subprocess.run(
                ["netsh", "interface", "set", "interface",
                 adapter_name, "enabled"],
                check=True,
                capture_output=True
            )
            
            time.sleep(1)  # Wait for the interface to be enabled
            
            # Use the exact command format that works manually, with proper spacing and no f-string
            command = ["netsh", "interface", "ip", "set", "address", 
                      "name=" + adapter_name, 
                      "static", 
                      ip_address, 
                      "255.255.255.0"]
            
            self.logger.info(f"Running command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True  # This will decode output as text
            )
            
            if result.stderr:
                self.logger.warning(f"Command stderr: {result.stderr}")
            if result.stdout:
                self.logger.info(f"Command stdout: {result.stdout}")
                
            self.logger.info(f"Configured TAP adapter '{adapter_name}' with IP {ip_address}")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to configure TAP adapter: {e}")
            error_msg = e.stderr if e.stderr else str(e)
            self.logger.error(f"Error details: {error_msg}")
            
            # Try alternative method with different command format
            try:
                alt_command = ["netsh", "interface", "ip", "set", "address",
                              adapter_name,  # Try without the "name=" prefix
                              "static",
                              ip_address,
                              "255.255.255.0"]
                
                self.logger.info(f"Trying alternative command: {' '.join(alt_command)}")
                
                subprocess.run(
                    alt_command,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                self.logger.info(f"Configured TAP adapter using alternative method")
                return
                
            except subprocess.CalledProcessError as e2:
                error_msg = e2.stderr if e2.stderr else str(e2)
                self.logger.error(f"Alternative method also failed: {error_msg}")
                raise RuntimeError(
                    f"Failed to configure TAP adapter. Please ensure you have administrator "
                    f"privileges and the TAP adapter is properly enabled. Error: {error_msg}"
                )
            
    def cleanup(self):
        """Cleanup TAP interface"""
        try:
            # Get the actual adapter name first
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-NetAdapter | Where-Object InterfaceDescription -like '*TAP-Windows*' | Select-Object -ExpandProperty Name"],
                capture_output=True,
                check=True
            )
            adapter_name = result.stdout.decode('utf-8').strip()
            
            if adapter_name:
                # Disable the adapter using the correct name
                subprocess.run(
                    ["netsh", "interface", "set", "interface",
                     adapter_name, "disabled"],
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"Disabled TAP adapter: {adapter_name}")
            else:
                self.logger.warning("No TAP adapter found during cleanup")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to cleanup TAP adapter: {e}")
            # Don't raise the error as cleanup should be best-effort
            
    def _install_tap_driver(self):
        """Install TAP driver"""
        try:
            # First try using Add-WindowsFeature
            try:
                subprocess.run(
                    ["powershell", "-Command", "Add-WindowsFeature -Name RSAT-Networking"],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                # If that fails, try using DISM
                subprocess.run(
                    ["DISM", "/Online", "/Enable-Feature", "/FeatureName:RSAT-Networking"],
                    check=True,
                    capture_output=True
                )
            
            self.logger.info("TAP driver installation initiated")
            self.needs_restart = True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install TAP driver: {e}")
            raise RuntimeError(
                "Failed to install TAP driver. Please ensure you're running as administrator "
                "and try again after restarting your computer."
            )

class LinuxInterfaceManager(VirtualInterfaceManager):
    def create_interface(self):
        try:
            subprocess.run(['sudo', 'ip', 'tuntap', 'add', 'dev', 'tap0', 'mode', 'tap'],
                         check=True)
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create TAP interface: {e}")

    def configure_interface(self, ip_address):
        try:
            subprocess.run(['sudo', 'ip', 'addr', 'add', f'{ip_address}/24', 'dev', 'tap0'],
                         check=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', 'tap0', 'up'], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to configure TAP interface: {e}")

    def cleanup(self):
        try:
            subprocess.run(['sudo', 'ip', 'tuntap', 'del', 'dev', 'tap0', 'mode', 'tap'],
                         check=True)
        except subprocess.CalledProcessError:
            pass
