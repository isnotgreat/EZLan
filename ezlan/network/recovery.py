from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time

class ConnectionRecoveryManager(QObject):
    recovery_started = pyqtSignal(str)  # user_name
    recovery_succeeded = pyqtSignal(str)  # user_name
    recovery_failed = pyqtSignal(str, str)  # user_name, error
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.recovery_attempts = {}
        self.max_attempts = 3
        self.retry_delay = 5  # seconds
        
    def start_recovery(self, user_name, connection_info):
        if user_name not in self.recovery_attempts:
            self.recovery_attempts[user_name] = {
                'attempts': 0,
                'info': connection_info
            }
            self.recovery_started.emit(user_name)
            threading.Thread(
                target=self._recovery_loop,
                args=(user_name,),
                daemon=True
            ).start()
    
    def _recovery_loop(self, user_name):
        while (user_name in self.recovery_attempts and 
               self.recovery_attempts[user_name]['attempts'] < self.max_attempts):
            try:
                info = self.recovery_attempts[user_name]['info']
                self.tunnel_service.reconnect_to_user(info)
                self.recovery_succeeded.emit(user_name)
                del self.recovery_attempts[user_name]
                return
            except Exception as e:
                self.recovery_attempts[user_name]['attempts'] += 1
                if self.recovery_attempts[user_name]['attempts'] >= self.max_attempts:
                    self.recovery_failed.emit(user_name, str(e))
                    del self.recovery_attempts[user_name]
                    return
                time.sleep(self.retry_delay)
