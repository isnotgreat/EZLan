from PyQt6.QtCore import QObject, pyqtSignal
import socket
import asyncio
from ..utils.logger import Logger
from .interface_manager import InterfaceManager
import aiohttp
from .secure_tunnel import SecureTunnel

class TunnelService(QObject):
    # Define all required signals
    host_started = pyqtSignal(dict)  # Emits host info when hosting starts
    host_failed = pyqtSignal(str)    # Emits error message when hosting fails
    interface_created = pyqtSignal(str)  # Emits interface name when created
    interface_error = pyqtSignal(str)    # Emits error message when interface creation fails
    connection_established = pyqtSignal(dict)  # Emits peer info when connected
    connection_failed = pyqtSignal(str)        # Emits error message when connection fails
    connection_closed = pyqtSignal(str)        # Emits peer name when disconnected

    def __init__(self):
        super().__init__()
        self.logger = Logger("TunnelService")
        self.interface_manager = InterfaceManager()
        self.active_tunnels = {}
        self.secure_tunnel = SecureTunnel(self)
        
        # Connect secure tunnel signals
        self.secure_tunnel.connection_established.connect(self._handle_secure_connection)
        self.secure_tunnel.connection_lost.connect(self._handle_connection_lost)

        # Connect interface manager signals
        self.interface_manager.interface_created.connect(self.on_interface_created)
        self.interface_manager.interface_error.connect(self.on_interface_error)

    def get_public_ip(self) -> str:
        """Synchronously retrieve the public IP address."""
        try:
            # Use a simple HTTP request to get IP
            import requests
            response = requests.get("https://api.ipify.org", timeout=5)
            if response.status_code == 200:
                return response.text.strip()
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

    async def start_hosting(self, host_info):
        """Start hosting a network"""
        try:
            # Get IP synchronously to avoid task conflicts
            public_ip = self.get_public_ip()
            
            # Merge provided host info with system info
            host_info.update({
                'public_ip': public_ip,
                'interface_name': self.interface_manager.interface_manager.interface_name
            })
            
            self.host_started.emit(host_info)
            self.logger.info(f"Started hosting on {public_ip}:{host_info['port']}")
            
        except Exception as e:
            self.logger.error(f"Failed to start hosting: {e}")
            self.host_failed.emit(str(e))
            raise

    def on_interface_created(self, interface_name):
        """Handle interface creation success"""
        self.interface_created.emit(interface_name)

    def on_interface_error(self, error_message):
        """Handle interface creation error"""
        self.interface_error.emit(error_message)

    async def stop_hosting(self):
        """Stop hosting and cleanup"""
        try:
            self.logger.info("Stopping hosting...")
            # Close all connections first
            for tunnel in list(self.active_tunnels.values()):
                try:
                    if 'socket' in tunnel:
                        tunnel['socket'].close()
                except Exception as e:
                    self.logger.error(f"Error closing socket: {e}")
            
            self.active_tunnels.clear()
            
            # Clean up interface
            try:
                if hasattr(self, 'interface_manager'):
                    await self.interface_manager.cleanup_interface()
            except Exception as e:
                self.logger.error(f"Error cleaning up interface: {e}")
                
            self.logger.info("Stopped hosting network.")
        except Exception as e:
            self.logger.error(f"Failed to stop hosting: {e}")

    def connect_to_peer(self, host: str, port: int, password: str = None):
        """Connect to a peer"""
        try:
            if self.secure_tunnel.create_connection(host, port):
                peer_info = {
                    'name': f"Peer-{host}",
                    'host': host,
                    'port': port
                }
                self.active_tunnels[peer_info['name']] = peer_info
                self.connection_established.emit(peer_info)
                self.logger.info(f"Connected to peer at {host}:{port}")
            else:
                error_msg = "Failed to establish secure connection"
                self.logger.error(error_msg)
                self.connection_failed.emit(error_msg)
        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}"
            self.logger.error(error_msg)
            self.connection_failed.emit(error_msg)

    def _handle_secure_connection(self, connection_info):
        """Handle successful secure connection"""
        self.logger.info(f"Secure connection established with {connection_info['host']}")

    def _handle_connection_lost(self, host):
        """Handle lost connection"""
        self.logger.info(f"Connection lost with {host}")
        self.connection_closed.emit(f"Peer-{host}")

    def disconnect_from_peer(self, peer_name: str):
        """Disconnect from a peer"""
        try:
            if peer_name in self.active_tunnels:
                del self.active_tunnels[peer_name]
                self.connection_closed.emit(peer_name)
                self.logger.info(f"Disconnected from {peer_name}")
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")

    async def connect_to_host(self, host: str, port: int, password: str = None):
        """Connect to a host with authentication"""
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await asyncio.get_event_loop().sock_connect(sock, (host, port))
            
            peer_info = {
                'name': f"Host-{host}",
                'host': host,
                'port': port,
                'socket': sock
            }
            
            self.active_tunnels[peer_info['name']] = peer_info
            self.connection_established.emit(peer_info)
            self.logger.info(f"Connected to host at {host}:{port}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to host: {str(e)}"
            self.logger.error(error_msg)
            self.connection_failed.emit(error_msg)
            return False



