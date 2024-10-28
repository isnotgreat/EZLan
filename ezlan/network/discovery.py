from PyQt6.QtCore import QObject, pyqtSignal
from ezlan.utils.logger import Logger
import netifaces
import socket
import json

class DiscoveryService(QObject):
    # Define signals
    peer_discovered = pyqtSignal(dict)    # Emits peer info when discovered
    peer_lost = pyqtSignal(str)           # Emits peer name when lost
    users_updated = pyqtSignal(list)      # Emits list of all current users
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("DiscoveryService")
        self.known_peers = {}
        self.broadcast_port = 5000
        self.setup_socket()
        
    def setup_socket(self):
        """Setup UDP socket for peer discovery"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.bind(('', self.broadcast_port))
            self.socket.setblocking(False)
            self.logger.info("Discovery socket setup complete")
        except Exception as e:
            self.logger.error(f"Failed to setup discovery socket: {e}")
            
    def start_discovery(self):
        """Start broadcasting presence and listening for peers"""
        try:
            # Broadcast presence
            self._broadcast_presence()
            # Start listening for other peers
            self._start_listening()
            self.logger.info("Discovery service started")
        except Exception as e:
            self.logger.error(f"Failed to start discovery: {e}")
            
    def _broadcast_presence(self):
        """Broadcast presence to network"""
        try:
            presence_data = {
                'name': socket.gethostname(),
                'ip': self._get_local_ip(),
                'type': 'presence'
            }
            message = json.dumps(presence_data).encode()
            self.socket.sendto(message, ('<broadcast>', self.broadcast_port))
        except Exception as e:
            self.logger.error(f"Failed to broadcast presence: {e}")
            
    def _start_listening(self):
        """Listen for peer broadcasts"""
        try:
            while True:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    peer_info = json.loads(data.decode())
                    
                    if peer_info['type'] == 'presence':
                        if peer_info['name'] not in self.known_peers:
                            self.known_peers[peer_info['name']] = peer_info
                            self.peer_discovered.emit(peer_info)
                            # Emit updated users list
                            self.users_updated.emit(list(self.known_peers.values()))
                            self.logger.info(f"Discovered peer: {peer_info['name']}")
                except BlockingIOError:
                    # No data available
                    break
        except Exception as e:
            self.logger.error(f"Error while listening for peers: {e}")
            
    def get_known_peers(self):
        """Get list of known peers"""
        return list(self.known_peers.values())
            
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            return ip
            return '127.0.0.1'  # Fallback to localhost
        except Exception as e:
            self.logger.error(f"Failed to get local IP: {e}")
            return '127.0.0.1'
            
    def stop_discovery(self):
        """Stop discovery service"""
        try:
            self.socket.close()
            self.logger.info("Discovery service stopped")
        except Exception as e:
            self.logger.error(f"Error stopping discovery service: {e}")

    def get_discovered_peers(self):
        """Return list of currently discovered peers"""
        return list(self.known_peers.values())
    
    def add_peer(self, peer_info):
        """Add or update a discovered peer"""
        peer_name = peer_info['name']
        if peer_name not in self.known_peers:
            self.known_peers[peer_name] = peer_info
            self.peer_discovered.emit(peer_info)
            self.logger.info(f"Discovered peer: {peer_name}")
    
    def remove_peer(self, peer_name):
        """Remove a peer that is no longer available"""
        if peer_name in self.known_peers:
            del self.known_peers[peer_name]
            self.peer_lost.emit(peer_name)
            self.logger.info(f"Lost peer: {peer_name}")
