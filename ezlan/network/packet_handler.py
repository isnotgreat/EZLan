from PyQt6.QtCore import QObject, pyqtSignal
import socket
import struct
import threading
from typing import Dict, Optional
from cryptography.fernet import Fernet
from ..utils.logger import Logger

class CustomNetworkInterface(QObject):
    packet_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.raw_socket = None
        self.bound_ip = None
        self.running = False
        self.packet_buffer_size = 65535
        self.gaming_ports = {3074, 3075, 27015, 27016, 7777, 8080}
        self.receive_thread = None
        self.packet_handlers = {}
        
    def initialize(self, ip_address: str) -> bool:
        try:
            # Create raw socket for custom network handling
            self.raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            self.raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            self.bound_ip = ip_address
            
            # Start packet receiver thread
            self.running = True
            self.receive_thread = threading.Thread(target=self._packet_receiver, daemon=True)
            self.receive_thread.start()
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize interface: {e}")
            return False

class SecurePacketHandler:
    def __init__(self, tunnel_service):
        self.tunnel_service = tunnel_service
        self.logger = Logger("SecurePacketHandler")
        self.gaming_ports = {3074, 3075, 27015, 27016, 7777, 8080}
        
    def handle_packet(self, encrypted_data: bytes, connection_info: dict) -> bool:
        try:
            # Decrypt packet
            data = Fernet(connection_info['encryption_key']).decrypt(encrypted_data)
            
            # Check for gaming packet
            if len(data) > 28:  # IP + UDP header
                dst_port = struct.unpack('!H', data[22:24])[0]
                if dst_port in self.gaming_ports:
                    return self._handle_gaming_packet(data, connection_info)
                    
            # Handle regular packet
            return self._handle_regular_packet(data, connection_info)
            
        except Exception as e:
            self.logger.error(f"Packet handling error: {e}")
            return False