from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
import threading
import time

@dataclass
class GamingRecoveryConfig:
    max_attempts: int = 5  # More attempts for gaming
    retry_delay: float = 2.0  # Faster retry for gaming
    connection_timeout: float = 3.0  # Shorter timeout
    packet_priority: int = 6  # High priority for gaming packets

class GamingRecoveryManager(QObject):
    recovery_started = pyqtSignal(str)  # user_name
    recovery_succeeded = pyqtSignal(str)  # user_name
    recovery_failed = pyqtSignal(str, str)  # user_name, error
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.recovery_config = GamingRecoveryConfig()
        self.active_recoveries = {}
        self.gaming_optimizer = self.tunnel_service.gaming_optimizer
        
    def start_recovery(self, user_name, connection_info):
        if user_name in self.active_recoveries:
            return
            
        self.active_recoveries[user_name] = {
            'attempts': 0,
            'info': connection_info,
            'last_metrics': self.gaming_optimizer._get_gaming_metrics(user_name)
        }
        
        self.recovery_started.emit(user_name)
        threading.Thread(
            target=self._gaming_recovery_loop,
            args=(user_name,),
            daemon=True
        ).start() 