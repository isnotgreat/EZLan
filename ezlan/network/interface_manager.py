from ctypes import *
import subprocess
import platform
import winreg
from pathlib import Path

class WindowsInterfaceManager(VirtualInterfaceManager):
    def __init__(self):
        self.tap_name = "EZLan-TAP"
        self.component_id = "tap0901"
        self.adapter_key = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
        self.installer = SystemInstaller()
        self.installer.check_and_setup()
        
    def create_interface(self):
        try:
            # Check if TAP adapter already exists
            if self._find_tap_adapter():
                return self.tap_name

            # Create new TAP adapter using devcon
            adapter_name = "TAP-Windows Adapter V9"
            subprocess.run([
                "netsh", "interface", "set", "interface",
                f'"{adapter_name}"', "newname=EZLan-TAP"
            ], check=True, capture_output=True)
            
            self._wait_for_interface()
            return self.tap_name
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create TAP interface: {e}")
            
    def configure_interface(self, ip_address):
        try:
            # Configure IP address
            subprocess.run([
                "netsh", "interface", "ip",
                "set", "address",
                f'name="{self.tap_name}"',
                "static", ip_address, "255.255.255.0"
            ], check=True, capture_output=True)
            
            # Enable the interface
            subprocess.run([
                "netsh", "interface", "set",
                "interface", f'"{self.tap_name}"',
                "admin=enable"
            ], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to configure TAP interface: {e}")
            
    def cleanup(self):
        try:
            subprocess.run([
                str(self.tapctl_path), "delete",
                "--name", self.tap_name
            ], check=True, capture_output=True, shell=True)
        except subprocess.CalledProcessError:
            pass
            
    def _find_tap_adapter(self):
        """Check if our TAP adapter exists"""
        try:
            result = subprocess.run([
                "netsh", "interface", "show", "interface",
                f'name="{self.tap_name}"'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
            
    def _wait_for_interface(self, timeout=10):
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["netsh", "interface", "show", "interface", f'"{self.tap_name}"'],
                    capture_output=True,
                    text=True
                )
                if self.tap_name in result.stdout:
                    return True
                time.sleep(0.5)
            except subprocess.CalledProcessError:
                time.sleep(0.5)
        raise RuntimeError("Timeout waiting for TAP interface to be ready")
