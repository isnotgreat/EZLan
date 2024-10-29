import socket
import requests
import xml.etree.ElementTree as ET
from ezlan.utils.logger import Logger

class UPnPClient:
    def __init__(self):
        self.logger = Logger("UPnPClient")
        self.gateway_url = None
        self.control_url = None
        self.service_type = None
        self._discover_gateway()
        
    def _discover_gateway(self):
        """Discover UPnP gateway using SSDP"""
        try:
            # Create SSDP discovery socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            # Send M-SEARCH request
            search_request = (
                'M-SEARCH * HTTP/1.1\r\n'
                'HOST: 239.255.255.250:1900\r\n'
                'MAN: "ssdp:discover"\r\n'
                'MX: 2\r\n'
                'ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n'
                '\r\n'
            )
            
            sock.sendto(search_request.encode(), ('239.255.255.250', 1900))
            
            # Receive response
            data, addr = sock.recvfrom(1024)
            response = data.decode()
            
            # Parse location URL
            for line in response.split('\r\n'):
                if line.lower().startswith('location:'):
                    self.gateway_url = line.split(':', 1)[1].strip()
                    break
                    
            if self.gateway_url:
                # Get control URL and service type from device description
                response = requests.get(self.gateway_url)
                root = ET.fromstring(response.text)
                
                # Find the WANIPConnection or WANPPPConnection service
                ns = {'ns': 'urn:schemas-upnp-org:device-1-0'}
                for service in root.findall('.//ns:service', ns):
                    service_type = service.find('ns:serviceType', ns).text
                    if 'WANIPConnection' in service_type or 'WANPPPConnection' in service_type:
                        self.service_type = service_type
                        control_path = service.find('ns:controlURL', ns).text
                        # Build absolute control URL
                        base_url = '/'.join(self.gateway_url.split('/')[:-1])
                        self.control_url = f"{base_url}{control_path}"
                        self.logger.info(f"Found UPnP gateway: {self.gateway_url}")
                        return True
                        
            self.logger.error("No compatible UPnP gateway found")
            return False
            
        except Exception as e:
            self.logger.error(f"UPnP discovery failed: {e}")
            return False
            
    def add_port_mapping(self, port: int) -> bool:
        """Add port mapping using UPnP"""
        if not self.gateway_url or not self.control_url or not self.service_type:
            self.logger.error("Gateway or control URL not set")
            return False
            
        try:
            # Get local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            
            # Create port mapping request
            soap_request = (
                '<?xml version="1.0"?>'
                '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                '<s:Body>'
                f'<u:AddPortMapping xmlns:u="{self.service_type}">'
                '<NewRemoteHost></NewRemoteHost>'
                f'<NewExternalPort>{port}</NewExternalPort>'
                '<NewProtocol>TCP</NewProtocol>'
                f'<NewInternalPort>{port}</NewInternalPort>'
                f'<NewInternalClient>{local_ip}</NewInternalClient>'
                '<NewEnabled>1</NewEnabled>'
                '<NewPortMappingDescription>EZLan</NewPortMappingDescription>'
                '<NewLeaseDuration>0</NewLeaseDuration>'
                '</u:AddPortMapping>'
                '</s:Body>'
                '</s:Envelope>'
            )
            
            # Send request
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': f'"{self.service_type}#AddPortMapping"'
            }
            
            response = requests.post(self.control_url, data=soap_request, headers=headers)
            
            if response.status_code == 200:
                self.logger.info(f"Port mapping added for port {port}")
                return True
            else:
                self.logger.error(f"Failed to add port mapping: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding port mapping: {e}")
            return False
            
    def remove_port_mapping(self, port: int) -> bool:
        """Remove port mapping using UPnP"""
        if not self.gateway_url or not self.control_url or not self.service_type:
            self.logger.error("Gateway or control URL not set")
            return False
            
        try:
            # Create port mapping removal request
            soap_request = (
                '<?xml version="1.0"?>'
                '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
                's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
                '<s:Body>'
                f'<u:DeletePortMapping xmlns:u="{self.service_type}">'
                '<NewRemoteHost></NewRemoteHost>'
                f'<NewExternalPort>{port}</NewExternalPort>'
                '<NewProtocol>TCP</NewProtocol>'
                '</u:DeletePortMapping>'
                '</s:Body>'
                '</s:Envelope>'
            )
            
            # Send request
            headers = {
                'Content-Type': 'text/xml',
                'SOAPAction': f'"{self.service_type}#DeletePortMapping"'
            }
            
            response = requests.post(self.control_url, data=soap_request, headers=headers)
            
            if response.status_code == 200:
                self.logger.info(f"Port mapping removed for port {port}")
                return True
            else:
                self.logger.error(f"Failed to remove port mapping: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing port mapping: {e}")
            return False