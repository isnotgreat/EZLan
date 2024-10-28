import subprocess
import socket
import win32com.client
import pythoncom
import logging
import sys

class NetworkConfigurator:
    def __init__(self):
        self.logger = logging.getLogger("NetworkConfigurator")
        self.upnp = None
        self.executable_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        
    def setup(self, port):
        """Setup both port forwarding and firewall rules"""
        success_port = self.setup_port_forwarding(port)
        success_firewall = self.setup_firewall_rules()
        return success_port and success_firewall

    def setup_port_forwarding(self, port):
        try:
            pythoncom.CoInitialize()
            self.upnp = win32com.client.Dispatch('HNetCfg.NATUPnP')
            
            # Check if we got a valid UPnP object
            if not self.upnp or not hasattr(self.upnp, 'StaticPortMappingCollection'):
                self.logger.warning("UPnP not available on this network")
                return True  # Continue without UPnP
                
            mapping_collection = self.upnp.StaticPortMappingCollection
            if mapping_collection is None:
                self.logger.warning("UPnP port mapping not supported by router")
                return True  # Continue without UPnP
                
            mapping_collection.Add(
                port, "TCP", port,
                socket.gethostbyname(socket.gethostname()),
                True, "EZLan"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup port forwarding: {e}")
            return True  # Continue even if port forwarding fails

    def setup_firewall_rules(self):
        try:
            # Add inbound rule
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name="EZLan"',
                'dir=in',
                'action=allow',
                f'program="{self.executable_path}"',
                'enable=yes'
            ], check=True, capture_output=True)

            # Add outbound rule
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name="EZLan"',
                'dir=out',
                'action=allow',
                f'program="{self.executable_path}"',
                'enable=yes'
            ], check=True, capture_output=True)
            
            self.logger.info("Firewall rules added successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup firewall rules: {e}")
            return False