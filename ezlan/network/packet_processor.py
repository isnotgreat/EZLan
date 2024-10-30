from PyQt6.QtCore import QObject, pyqtSignal
import socket
import struct
import threading
from typing import Dict, Optional
from .packet_router import PacketRouter
from ..utils.logger import Logger
from queue import Queue

class CustomNetworkInterface(QObject):
    packet_received = pyqtSignal(bytes)
    connection_status = pyqtSignal(str, str)  # status, message
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("CustomNetworkInterface")
        self.raw_socket = None
        self.bound_ip = None
        self.running = False
        self.packet_router = PacketRouter()
        self.gaming_ports = {3074, 3075, 27015, 27016, 7777, 8080}
        self.monitor = self._setup_monitoring()
        
    def initialize(self, ip_address: str) -> bool:
        try:
            # Create raw socket with IP header included
            if hasattr(socket, 'AF_PACKET'):
                self.raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
            else:
                self.raw_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
                self.raw_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            
            self.bound_ip = ip_address
            self._setup_optimizations()
            self._start_packet_handler()
            return True
            
        except Exception as e:
            self.logger.error(f"Interface initialization failed: {e}")
            return False

class PacketProcessor:
    def __init__(self, interface):
        self.interface = interface
        self.logger = Logger("PacketProcessor")
        self.gaming_ports = interface.gaming_ports
        self.packet_queue = Queue(maxsize=1000)
        self.processing_thread = None
        
    def start(self):
        self.processing_thread = threading.Thread(target=self._process_packets, daemon=True)
        self.processing_thread.start()
        
    def _process_packets(self):
        while True:
            try:
                packet = self.packet_queue.get()
                if self._is_gaming_packet(packet):
                    self._handle_gaming_packet(packet)
                else:
                    self._handle_regular_packet(packet)
                    
            except Exception as e:
                self.logger.error(f"Packet processing error: {e}")
                continue 