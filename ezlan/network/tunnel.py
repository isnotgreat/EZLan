import socket
import threading
import struct
import os
from PyQt6.QtCore import QObject, pyqtSignal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from ezlan.network.virtual_interface import WindowsInterfaceManager, LinuxInterfaceManager
import platform
import ipaddress
from ezlan.network.packet_router import PacketRouter
from ezlan.utils.logger import Logger
from ezlan.network.bandwidth_monitor import BandwidthMonitor
from ezlan.network.security import SecurityManager
from ezlan.network.quality_monitor import QualityMonitor
from ezlan.network.recovery import ConnectionRecoveryManager
from ezlan.network.nat_traversal import NATTraversal
from ezlan.network.traffic_shaper import TrafficShaper, QoSPolicy
from ezlan.network.bandwidth_allocator import BandwidthAllocator
from ezlan.network.performance_analytics import NetworkAnalytics
from ezlan.network.predictive_optimizer import PredictiveOptimizer
from ezlan.network.auto_optimizer import AutoOptimizer
from .analytics import NetworkAnalytics
import subprocess
import sys
from pathlib import Path
from ezlan.utils.installer import SystemInstaller
from ezlan.network.network_config import NetworkConfigurator
from ezlan.network.signaling import SignalingService
import qasync
import json

class TunnelService(QObject):
    connection_established = pyqtSignal(dict)  # Emits peer info when connected
    connection_failed = pyqtSignal(str)        # Emits error message on failure
    connection_closed = pyqtSignal(str)        # Emits peer name when disconnected
    host_started = pyqtSignal(dict)  # Emits host info including public IP and port
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("TunnelService")
        self.active_tunnels = {}
        self.encryption_key = None
        self.tunnel_port = 12345
        self.is_hosting = False
        self.host_info = None
        self.interface_manager = self._get_interface_manager()
        self.network_pool = ipaddress.IPv4Network('10.0.0.0/24')
        self.used_ips = set()
        
        # Default bandwidth in bytes per second (100 Mbps)
        self.default_bandwidth = 100 * 1024 * 1024  
        
        # Initialize services in correct order with dependencies
        self.network_analytics = NetworkAnalytics()
        self.bandwidth_monitor = BandwidthMonitor()
        self.security_manager = SecurityManager()
        self.quality_monitor = QualityMonitor()
        self.nat_traversal = NATTraversal()
        self.traffic_shaper = TrafficShaper()
        self.bandwidth_allocator = BandwidthAllocator(total_bandwidth=self.default_bandwidth)
        
        # Initialize services that need self reference
        self.recovery_manager = ConnectionRecoveryManager(tunnel_service=self)
        self.predictive_optimizer = PredictiveOptimizer(tunnel_service=self)
        self.auto_optimizer = AutoOptimizer(tunnel_service=self)
        
        # Start services
        self.setup_services()
        
        # Get public IP after NAT traversal is initialized
        self.public_ip = self.nat_traversal.get_public_ip()
        
        # Initialize network analytics
        self.network_analytics.start()
        self.logger.info("Network analytics service started")
        
        # Add to existing init
        self.signaling = SignalingService()
        
    def _get_interface_manager(self):
        system = platform.system().lower()
        if system == 'windows':
            return WindowsInterfaceManager()
        elif system == 'linux':
            return LinuxInterfaceManager()
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")

    def _allocate_ip(self):
        for ip in self.network_pool.hosts():
            if str(ip) not in self.used_ips:
                self.used_ips.add(str(ip))
                return str(ip)
        raise RuntimeError("No available IP addresses")

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.tunnel_port))
        self.server_socket.listen(5)
        
        threading.Thread(target=self._accept_connections, daemon=True).start()
        
    def _accept_connections(self):
        """Background thread to accept incoming connections"""
        while self.is_hosting:
            try:
                if not hasattr(self, 'server_socket') or self.server_socket._closed:
                    break
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"New connection from {client_address}")
                
                # Handle authentication and connection setup in a new thread
                threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, client_address),
                    daemon=True
                ).start()
                
            except socket.error as e:
                if not self.is_hosting:  # Expected when stopping
                    break
                self.logger.error(f"Accept error: {e}")
                continue

    def _handle_client_connection(self, client_socket, client_address):
        """Handle new client connection"""
        try:
            if not self._authenticate_client(client_socket, client_address):
                client_socket.close()
                return
                
            # Start tunnel for authenticated client
            local_ip = self._allocate_ip()
            self.interface_manager.setup_interface(local_ip)
            self._start_tunnel(client_socket, local_ip)
            
            # Add to active tunnels
            self.active_tunnels[client_address[0]] = {
                'socket': client_socket,
                'ip': local_ip,
                'status': 'connected'
            }
            
            self.connection_established.emit({
                'name': client_address[0],
                'ip': client_address[0]
            })
            
        except Exception as e:
            self.logger.error(f"Error handling client connection: {e}")
            if not client_socket._closed:
                client_socket.close()

    def _setup_secure_channel(self, socket):
        try:
            # Exchange public keys
            socket.send(
                self.security_manager.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )
            peer_public_key_bytes = socket.recv(2048)
            peer_public_key = serialization.load_pem_public_key(peer_public_key_bytes)
            
            # Generate and exchange session key
            session_key = self.security_manager.generate_session_key(self.password)
            encrypted_session_key = self.security_manager.encrypt_session_key(
                session_key, 
                peer_public_key
            )
            socket.send(encrypted_session_key)
            
            self.encryption_key = session_key
            return True
        except Exception as e:
            self.logger.error(f"Secure channel setup failed: {e}")
            return False
            
    def _forward_packets(self, socket):
        while True:
            try:
                # Read packet header (size)
                size_data = socket.recv(4)
                if not size_data:
                    break
                    
                size = struct.unpack('!I', size_data)[0]
                
                # Read encrypted packet
                encrypted_data = socket.recv(size)
                if not encrypted_data:
                    break
                
                # Decrypt packet
                data = Fernet(self.encryption_key).decrypt(encrypted_data)
                
                # Enqueue packet for traffic shaping
                self.traffic_shaper.enqueue_packet(
                    self.current_user['name'],
                    data
                )
                
                # Process shaped packets
                for shaped_packet in self.traffic_shaper._process_queue(self.current_user['name']):
                    self._write_to_virtual_interface(shaped_packet)
                    
            except Exception as e:
                self.logger.error(f"Error forwarding packets: {e}")
                break
                
    def connect_to_user(self, user_info, password):
        try:
            # Get public endpoint
            public_ip, public_port = self.nat_traversal.get_public_endpoint()
            
            # Punch hole in NAT
            local_port = self.nat_traversal.punch_hole(user_info)
            
            # Store connection info for recovery
            connection_info = {
                'user_info': user_info,
                'password': password,
                'local_port': local_port,
                'public_endpoint': (public_ip, public_port)
            }
            
            # Attempt connection
            self._establish_connection(connection_info)
            
            # Setup QoS policy
            policy = QoSPolicy(
                priority=5,  # Default priority
                bandwidth_limit=1024*1024,  # 1 MB/s
                latency_target=50  # 50ms target latency
            )
            self.traffic_shaper.add_connection(user_info['name'], policy)
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.connection_failed.emit(str(e))
            raise

    def disconnect(self, user_name):
        if user_name in self.active_tunnels:
            tunnel_info = self.active_tunnels[user_name]
            tunnel_info['tunnel'].close()
            self.used_ips.remove(tunnel_info['ip'])
            del self.active_tunnels[user_name]
            self.interface_manager.cleanup()

    def update_qos_policy(self, user_name, policy):
        if user_name in self.active_tunnels:
            self.traffic_shaper.update_policy(user_name, policy)
            self.logger.info(f"Updated QoS policy for {user_name}: {vars(policy)}")

    async def start_hosting(self, name: str, password: str, port: int = None):
        """Start hosting a network"""
        try:
            if port is None:
                port = self.tunnel_port
                
            # Initialize network configurator
            self.network_config = NetworkConfigurator()
            
            # Setup port forwarding and firewall rules
            if not self.network_config.setup(port):
                self.logger.warning("Network configuration partially failed")
                
            # Start server
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            self.is_hosting = True
            
            # Start accepting connections
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
            # Get public IP
            public_ip = self.nat_traversal.get_public_ip()
            
            self.host_info = {
                'name': name,
                'password': password,
                'public_ip': public_ip,
                'port': port
            }
            
            self.host_started.emit(self.host_info)
            self.logger.info(f"Started hosting on {public_ip}:{port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start hosting: {e}")
            raise

    @qasync.asyncSlot(str, int, str)
    async def connect_to_host(self, host_ip: str, port: int, password: str) -> bool:
        """Connect to a hosted network"""
        try:
            self.logger.info(f"Attempting to connect to {host_ip}:{port}")
            
            # Create connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host_ip, port))
            
            # Wait for auth request
            auth_request = json.loads(sock.recv(1024).decode())
            if auth_request.get('type') != 'auth_request':
                raise RuntimeError("Invalid server response")
                
            # Send authentication
            sock.send(json.dumps({
                'password': password
            }).encode())
            
            # Get response
            response = json.loads(sock.recv(1024).decode())
            if response.get('status') != 'success':
                raise RuntimeError("Authentication failed")
                
            # Setup interface and tunnel
            local_ip = response.get('ip')
            self.interface_manager.setup_interface(local_ip)
            self._start_tunnel(sock, local_ip)
            
            self.connection_established.emit({
                'name': host_ip,
                'ip': host_ip
            })
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Connection failed: {error_msg}")
            self.connection_failed.emit(error_msg)
            return False

    def setup_services(self):
        """Initialize required services"""
        try:
            # Initialize network analytics
            self.network_analytics.start()
            self.logger.info("Network analytics service started")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            
    def connect_to_peer(self, peer_info: dict):
        """Establish connection with a peer"""
        try:
            peer_name = peer_info['name']
            peer_ip = peer_info['ip']
            
            if peer_name in self.active_tunnels:
                self.logger.warning(f"Already connected to {peer_name}")
                return
                
            # TODO: Implement actual tunnel establishment
            # For now, just simulate successful connection
            self.active_tunnels[peer_name] = {
                'name': peer_name,
                'ip': peer_ip,
                'status': 'connected'
            }
            
            self.connection_established.emit(peer_info)
            self.logger.info(f"Connected to peer: {peer_name}")
            
        except Exception as e:
            error_msg = f"Failed to connect to peer: {str(e)}"
            self.connection_failed.emit(error_msg)
            self.logger.error(error_msg)
            
    def disconnect_from_peer(self, peer_name: str):
        """Disconnect from a peer"""
        try:
            if peer_name in self.active_tunnels:
                # TODO: Implement actual tunnel teardown
                del self.active_tunnels[peer_name]
                self.connection_closed.emit(peer_name)
                self.logger.info(f"Disconnected from peer: {peer_name}")
            else:
                self.logger.warning(f"No active connection to {peer_name}")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting from peer: {e}")
            
    def get_connection_status(self, peer_name: str) -> str:
        """Get the status of connection to a peer"""
        if peer_name in self.active_tunnels:
            return self.active_tunnels[peer_name]['status']
        return 'disconnected'
        
    def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Disconnect all peers
            for peer_name in list(self.active_tunnels.keys()):
                self.disconnect_from_peer(peer_name)
                
            # Stop analytics
            self.network_analytics.stop()
            self.logger.info("Tunnel service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def stop_hosting(self):
        """Stop hosting and cleanup"""
        try:
            self.is_hosting = False  # Set this first to stop accept loop
            
            # Close server socket if it exists and is open
            if hasattr(self, 'server_socket') and not self.server_socket._closed:
                try:
                    self.server_socket.shutdown(socket.SHUT_RDWR)
                    self.server_socket.close()
                except Exception as e:
                    self.logger.debug(f"Error closing server socket: {e}")
            
            # Disconnect all clients
            for peer_name in list(self.active_tunnels.keys()):
                try:
                    self.disconnect_from_peer(peer_name)
                except Exception as e:
                    self.logger.debug(f"Error disconnecting peer {peer_name}: {e}")
            
            # Remove port forwarding
            if hasattr(self, 'network_config'):
                try:
                    self.network_config.remove_port_forwarding(self.tunnel_port)
                except Exception as e:
                    self.logger.debug(f"Error removing port forwarding: {e}")
            
            # Reset host info
            self.host_info = None
            
            self.logger.info("Stopped hosting")
            
        except Exception as e:
            self.logger.error(f"Error stopping host: {e}")
        finally:
            # Ensure these are always reset
            self.is_hosting = False
            if hasattr(self, 'server_socket'):
                delattr(self, 'server_socket')

    def _start_tunnel(self, sock, local_ip):
        """Start the network tunnel"""
        try:
            # Create and configure TAP interface
            interface_name = self.interface_manager.create_interface()
            self.interface_manager.configure_interface(local_ip)
            
            # Start packet forwarding
            self._start_packet_forwarding(sock, interface_name)
            
            # Add routes for game traffic
            self._configure_routes(interface_name)
            
            return interface_name
            
        except Exception as e:
            raise RuntimeError(f"Failed to start tunnel: {e}")

    def _configure_routes(self, interface_name):
        """Configure routing for game traffic"""
        try:
            if sys.platform == 'win32':
                subprocess.run([
                    'route', 'add',
                    self.network_pool.network_address,
                    'mask', self.network_pool.netmask,
                    interface_name
                ], check=True)
            else:
                subprocess.run([
                    'sudo', 'ip', 'route', 'add',
                    f"{self.network_pool.network_address}/{self.network_pool.prefixlen}",
                    'dev', interface_name
                ], check=True)
        except Exception as e:
            self.logger.error(f"Failed to configure routes: {e}")

    def _authenticate_client(self, client_socket, client_address):
        """Authenticate incoming client connection"""
        try:
            # Set timeout for authentication
            client_socket.settimeout(10)
            
            # Send auth request
            client_socket.send(json.dumps({
                'type': 'auth_request'
            }).encode())
            
            # Receive authentication data
            auth_data = client_socket.recv(1024).decode()
            try:
                auth_info = json.loads(auth_data)
                password = auth_info.get('password')
            except json.JSONDecodeError:
                self.logger.error(f"Invalid authentication data from {client_address}")
                return False
                
            # Verify password
            if not password or password != self.host_info['password']:
                self.logger.error(f"Authentication failed for {client_address}")
                return False
                
            # Send success response
            client_socket.send(json.dumps({
                'status': 'success',
                'ip': self._allocate_ip()
            }).encode())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False



