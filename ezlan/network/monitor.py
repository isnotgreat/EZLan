from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
import ping3

class ConnectionMonitor(QObject):
    status_changed = pyqtSignal(str, bool)  # user_name, is_connected
    latency_updated = pyqtSignal(str, float)  # user_name, latency_ms

    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.active_monitors = {}
        self.running = True

    def start_monitoring(self, user_name, ip_address):
        if user_name not in self.active_monitors:
            self.active_monitors[user_name] = ip_address
            threading.Thread(target=self._monitor_connection,
                           args=(user_name, ip_address),
                           daemon=True).start()

    def stop_monitoring(self, user_name):
        if user_name in self.active_monitors:
            del self.active_monitors[user_name]

    def _monitor_connection(self, user_name, ip_address):
        consecutive_failures = 0
        while self.running and user_name in self.active_monitors:
            try:
                latency = ping3.ping(ip_address, timeout=1)
                if latency is not None:
                    consecutive_failures = 0
                    self.latency_updated.emit(user_name, latency * 1000)
                    self.status_changed.emit(user_name, True)
                else:
                    consecutive_failures += 1
            except Exception:
                consecutive_failures += 1

            if consecutive_failures >= 3:
                self.status_changed.emit(user_name, False)

            time.sleep(1)
