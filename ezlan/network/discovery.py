from PyQt6.QtCore import QObject, pyqtSignal
from ezlan.utils.logger import Logger
import netifaces
import socket
import json
import threading
import time

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
        self.PORT = 12346  # Define discovery port
        self._running = False
        self._discovery_thread = None
        self.setup_socket()
        
    def setup_socket(self):
        """Setup UDP socket for peer discovery"""
        try:
            # Close existing socket if it exists
            if hasattr(self, 'socket'):
                try:
                    self.socket.close()
                except:
                    pass

            # Create new socket with proper permissions
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Try different ports if the default one is in use
            ports_to_try = [self.broadcast_port, 0]  # Try specified port, then let OS choose
            for port in ports_to_try:
                try:
                    self.socket.bind(('0.0.0.0', port))
                    if port == 0:
                        self.broadcast_port = self.socket.getsockname()[1]
                    break
                except OSError as e:
                    if port == ports_to_try[-1]:  # Last attempt failed
                        raise
                    continue
                    
            self.socket.setblocking(False)
            self.logger.info(f"Discovery socket setup complete on port {self.broadcast_port}")
        except Exception as e:
            self.logger.error(f"Failed to setup discovery socket: {e}")
            raise
        
    def start_discovery(self):
        try:
            if hasattr(self, 'socket'):
                self.stop_discovery()  # Clean up existing socket
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.socket.bind(('', self.PORT))
            except OSError as e:
                if e.errno == 10048:  # Address already in use
                    self.logger.warning("Discovery port already in use, trying alternative")
                    self.socket.bind(('', 0))  # Let OS choose port
                    
            self.socket.setblocking(False)
            self._running = True
            self._discovery_thread = threading.Thread(target=self._discovery_loop)
            self._discovery_thread.daemon = True
            self._discovery_thread.start()
            self.logger.info("Discovery service started")
        except Exception as e:
            self.logger.error(f"Failed to setup discovery socket: {e}")
            self._running = False
            
    def _broadcast_presence(self):
        """Broadcast presence to network"""
        try:
            presence_data = {
                'name': socket.gethostname(),
                'ip': self._get_local_ip(),
                'type': 'presence'
            }
            message = json.dumps(presence_data).encode()
            
            # Use a separate socket for broadcasting
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                broadcast_socket.sendto(message, ('<broadcast>', self.broadcast_port))
            finally:
                broadcast_socket.close()
            
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

    def _discovery_loop(self):
        """Background loop for discovery service"""
        while self._running:
            try:
                self._broadcast_presence()
                self._start_listening()
                time.sleep(1)  # Wait before next iteration
            except Exception as e:
                self.logger.error(f"Error in discovery loop: {e}")
                time.sleep(1)  # Prevent tight loop on error
