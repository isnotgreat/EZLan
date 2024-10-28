from PyQt6.QtCore import QObject, pyqtSignal
import time
from collections import deque
from threading import Lock

class BandwidthMonitor(QObject):
    bandwidth_updated = pyqtSignal(str, float, float)  # user, upload_speed, download_speed
    
    def __init__(self):
        super().__init__()
        self.connections = {}
        self.lock = Lock()
        
    def add_connection(self, user_name):
        with self.lock:
            self.connections[user_name] = {
                'upload_bytes': deque(maxlen=10),
                'download_bytes': deque(maxlen=10),
                'last_update': time.time()
            }
    
    def update_bytes(self, user_name, upload_bytes, download_bytes):
        with self.lock:
            if user_name in self.connections:
                now = time.time()
                elapsed = now - self.connections[user_name]['last_update']
                
                # Calculate speeds in KB/s
                upload_speed = upload_bytes / elapsed / 1024
                download_speed = download_bytes / elapsed / 1024
                
                # Store measurements
                self.connections[user_name]['upload_bytes'].append(upload_speed)
                self.connections[user_name]['download_bytes'].append(download_speed)
                self.connections[user_name]['last_update'] = now
                
                # Calculate average speeds
                avg_upload = sum(self.connections[user_name]['upload_bytes']) / len(
                    self.connections[user_name]['upload_bytes'])
                avg_download = sum(self.connections[user_name]['download_bytes']) / len(
                    self.connections[user_name]['download_bytes'])
                
                self.bandwidth_updated.emit(user_name, avg_upload, avg_download)
