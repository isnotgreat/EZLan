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

class ConnectionStateMonitor:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.monitoring = True
        self.check_interval = 1.0  # 1 second
        self._start_monitoring()
        
    def _start_monitoring(self):
        def monitor_loop():
            while self.monitoring:
                current_time = time.time()
                for user_name, state in self.connection_manager.connections.items():
                    if current_time - state.last_seen > 5:  # 5 seconds timeout
                        self._handle_connection_timeout(user_name, state)
                time.sleep(self.check_interval)
                
        threading.Thread(target=monitor_loop, daemon=True).start()
        
    def _handle_connection_timeout(self, user_name: str, state: ConnectionState):
        if state.retry_count < self.connection_manager.max_retries:
            self._attempt_recovery(user_name, state)
        else:
            self.connection_manager.state_changed.emit(user_name, "disconnected") 