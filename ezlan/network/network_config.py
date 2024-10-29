import logging
import socket
import subprocess
import sys
from ezlan.network.upnp import UPnPClient
from ezlan.utils.logger import Logger

class NetworkConfigurator:
    def __init__(self):
        self.logger = Logger("NetworkConfigurator")
        self.upnp = None
        
    def setup(self, port):
        """Setup network configuration"""
        try:
            # Setup firewall rules
            success_firewall = self.setup_firewall_rules()
            
            # Try UPnP if available, but don't fail if it doesn't work
            try:
                success_upnp = self.setup_port_forwarding(port)
                if not success_upnp:
                    self.logger.warning("UPnP setup failed - continuing without port forwarding")
            except Exception as e:
                self.logger.warning(f"UPnP not available: {e} - continuing without port forwarding")
                success_upnp = True  # Don't fail the overall setup
                
            return success_firewall
            
        except Exception as e:
            self.logger.error(f"Network configuration failed: {e}")
            return False

    def setup_firewall_rules(self):
        """Setup Windows Firewall rules"""
        try:
            app_path = sys.executable
            
            # Add inbound rule for the port
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name="EZLan_TCP"',
                'dir=in',
                'action=allow',
                'protocol=TCP',
                'enable=yes'
            ], check=True)
            
            # Add outbound rule for the port
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name="EZLan_TCP"',
                'dir=out',
                'action=allow',
                'protocol=TCP',
                'enable=yes'
            ], check=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup firewall rules: {e}")
            return False

    def setup_port_forwarding(self, port):
        """Setup port forwarding using UPnP"""
        try:
            # Only try UPnP if we haven't already failed
            if self.upnp is None:
                self.upnp = UPnPClient()
                
            if self.upnp and self.upnp.add_port_mapping(port):
                self.logger.info(f"Successfully set up port forwarding for port {port}")
                return True
                
            return False
            
        except Exception as e:
            self.logger.warning(f"Port forwarding setup failed: {e}")
            return False

    def remove_port_forwarding(self, port):
        """Remove port forwarding"""
        try:
            if self.upnp:
                self.upnp.remove_port_mapping(port)
                self.logger.info(f"Removed port forwarding for port {port}")
        except Exception as e:
            self.logger.warning(f"Failed to remove port forwarding: {e}")

    def cleanup(self):
        """Cleanup network configuration"""
        try:
            # Remove firewall rules
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                'name="EZLan_TCP"'
            ], check=False)
            
            self.logger.info("Network configuration cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup network configuration: {e}")