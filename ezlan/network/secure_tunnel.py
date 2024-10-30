from PyQt6.QtCore import QObject, pyqtSignal
import socket
import threading
import json
from cryptography.fernet import Fernet
from ..utils.logger import Logger

class SecureTunnel(QObject):
    connection_established = pyqtSignal(dict)
    connection_lost = pyqtSignal(str)
    data_received = pyqtSignal(bytes)
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.logger = Logger("SecureTunnel")
        self.active_connections = {}
        self.packet_handlers = {}
        
    def create_connection(self, host: str, port: int) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            
            if self._setup_secure_channel(sock):
                connection_info = {
                    'socket': sock,
                    'host': host,
                    'port': port,
                    'status': 'connected'
                }
                self.active_connections[host] = connection_info
                self._start_packet_handler(host)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False 

    def _setup_secure_channel(self, sock):
        """Setup secure channel with authentication"""
        try:
            # Generate session key
            key = Fernet.generate_key()
            f = Fernet(key)
            
            # Exchange keys and authenticate
            sock.send(key)
            response = sock.recv(1024)
            
            if response:
                # Verify connection
                test_message = f.encrypt(b"connection_test")
                sock.send(test_message)
                verification = sock.recv(1024)
                
                return verification == b"verified"
                
            return False
        except Exception as e:
            self.logger.error(f"Failed to setup secure channel: {e}")
            return False

    def _start_packet_handler(self, host):
        """Start packet handler thread"""
        handler = threading.Thread(
            target=self._handle_packets,
            args=(host,),
            daemon=True
        )
        handler.start()