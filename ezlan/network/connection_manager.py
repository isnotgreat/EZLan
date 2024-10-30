from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
from typing import Dict, Optional
import threading
import time

@dataclass
class ConnectionState:
    ip_address: str
    port: int
    encryption_key: bytes
    interface_name: str
    is_gaming: bool
    last_seen: float
    retry_count: int

class ConnectionManager(QObject):
    state_changed = pyqtSignal(str, str)  # user_name, new_state
    connection_recovered = pyqtSignal(str)  # user_name
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.connections: Dict[str, ConnectionState] = {}
        self.recovery_threads: Dict[str, threading.Thread] = {}
        self.max_retries = 3
        self.retry_delay = 2
        
    def register_connection(self, user_name: str, connection_info: dict):
        self.connections[user_name] = ConnectionState(
            ip_address=connection_info['ip'],
            port=connection_info['port'],
            encryption_key=connection_info['encryption_key'],
            interface_name=connection_info['interface_name'],
            is_gaming=False,
            last_seen=time.time(),
            retry_count=0
        ) 