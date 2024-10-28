import socket
import requests
from ezlan.utils.logger import Logger

class NATTraversal:
    def __init__(self):
        self.logger = Logger("NATTraversal")
        self.stun_servers = [
            'stun.l.google.com:19302',
            'stun1.l.google.com:19302',
            'stun2.l.google.com:19302'
        ]
        
    def get_public_ip(self) -> str:
        """Get the public IP address using external services"""
        try:
            # Try multiple IP lookup services
            services = [
                'https://api.ipify.org',
                'https://api.my-ip.io/ip',
                'https://ip.seeip.org'
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        return response.text.strip()
                except:
                    continue
                    
            # Fallback to local IP if all services fail
            return self._get_local_ip()
            
        except Exception as e:
            self.logger.error(f"Failed to get public IP: {e}")
            return self._get_local_ip()
            
    def _get_local_ip(self) -> str:
        """Get local IP address as fallback"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
            
    def get_public_endpoint(self) -> tuple:
        """Get public IP and port using STUN"""
        try:
            # Try each STUN server
            for stun_server in self.stun_servers:
                try:
                    host, port = stun_server.split(':')
                    public_ip, public_port = self._stun_request(host, int(port))
                    if public_ip and public_port:
                        return (public_ip, public_port)
                except:
                    continue
                    
            # Fallback to simple public IP lookup
            return (self.get_public_ip(), 0)
            
        except Exception as e:
            self.logger.error(f"Failed to get public endpoint: {e}")
            return (self._get_local_ip(), 0)
            
    def punch_hole(self, peer_info: dict) -> int:
        """Punch hole in NAT for peer connection"""
        try:
            # Create UDP socket for hole punching
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', 0))
            local_port = sock.getsockname()[1]
            
            # Send packet to peer to punch hole
            sock.sendto(b'punch', (peer_info['ip'], peer_info.get('port', 12345)))
            
            # Keep socket open in background
            sock.setblocking(False)
            
            return local_port
            
        except Exception as e:
            self.logger.error(f"Failed to punch NAT hole: {e}")
            return 0
            
    def _stun_request(self, host: str, port: int) -> tuple:
        """Send STUN request to get public endpoint"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            sock.sendto(b'', (host, port))
            response = sock.recvfrom(1024)
            sock.close()
            
            # Parse STUN response (simplified)
            return (response[1][0], response[1][1])
            
        except Exception as e:
            self.logger.error(f"STUN request failed: {e}")
            return (None, None)
