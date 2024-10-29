import socket
import requests
import asyncio
from ezlan.utils.logger import Logger

class NATTraversal:
    def __init__(self):
        self.logger = Logger("NATTraversal")
        self.stun_servers = [
            ('stun.l.google.com', 19302),
            ('stun1.l.google.com', 19302),
            ('stun2.l.google.com', 19302)
        ]
        
    async def establish_connection(self, host_ip, port, password):
        """Try multiple connection methods"""
        methods = [
            self._try_direct_connection,
            self._try_hole_punching
        ]
        
        for method in methods:
            try:
                connection = await method(host_ip, port, password)
                if connection:
                    self.logger.info(f"Connection established using {method.__name__}")
                    return connection
            except Exception as e:
                self.logger.debug(f"{method.__name__} failed: {e}")
                continue
                
        raise RuntimeError("All connection methods failed")

    async def _try_direct_connection(self, host_ip, port, password):
        """Try direct TCP connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((host_ip, port))
            return sock
        except:
            sock.close()
            return None

    async def _try_hole_punching(self, host_ip, port, password):
        """Try UDP hole punching followed by TCP connection"""
        # Get our public endpoint
        public_ip, public_port = await self._get_public_endpoint()
        if not public_ip:
            return None
            
        # Create UDP socket for hole punching
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('0.0.0.0', 0))
        
        try:
            # Send hole punching packets
            for _ in range(3):
                udp_sock.sendto(b'punch', (host_ip, port))
                await asyncio.sleep(0.1)
            
            # Try TCP connection
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(5)
            tcp_sock.connect((host_ip, port))
            return tcp_sock
            
        except:
            return None
        finally:
            udp_sock.close()

    async def _get_public_endpoint(self):
        """Get public IP and port using STUN"""
        for stun_server in self.stun_servers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(b'', stun_server)
                response = sock.recvfrom(1024)
                sock.close()
                return response[1]
            except:
                continue
        return None, None

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
                        ip = response.text.strip()
                        self.logger.info(f"Got public IP: {ip}")
                        return ip
                except Exception as e:
                    self.logger.debug(f"Service {service} failed: {e}")
                    continue
                
            # If all services fail, fall back to local IP
            local_ip = self._get_local_ip()
            self.logger.warning(f"Failed to get public IP, using local IP: {local_ip}")
            return local_ip
            
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
