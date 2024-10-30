from PyQt6.QtCore import QObject, pyqtSignal
import time
from collections import deque
from threading import Lock
import threading
from ezlan.utils.logger import Logger

class BandwidthMonitor(QObject):
    bandwidth_updated = pyqtSignal(str, float, float)  # user, upload_speed, download_speed
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("BandwidthMonitor")
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 1.0  # 1 second update interval
        
    def start(self):
        """Start bandwidth monitoring"""
        try:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Bandwidth monitoring started")
        except Exception as e:
            self.logger.error(f"Failed to start bandwidth monitoring: {e}")
            raise
            
    def stop(self):
        """Stop bandwidth monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Bandwidth monitoring stopped")
        
    def add_connection(self, user_name):
        with self._lock:
            self.connections[user_name] = {
                'upload_bytes': deque(maxlen=10),
                'download_bytes': deque(maxlen=10),
                'last_update': time.time()
            }
    
    def update_bytes(self, user_name, upload_bytes, download_bytes):
        with self._lock:
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

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    # Check for stale connections
                    for conn_id, conn in list(self.connections.items()):
                        if now - conn['last_update'] > 10.0:  # 10 second timeout
                            self.logger.warning(f"Connection {conn_id} timed out")
                            del self.connections[conn_id]
                            
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
