from PyQt6.QtCore import QObject, pyqtSignal
import time
from collections import deque
import statistics

class QualityMonitor(QObject):
    quality_updated = pyqtSignal(str, dict)  # user_name, metrics
    
    def __init__(self):
        super().__init__()
        self.connections = {}
        self.window_size = 50
        
    def add_connection(self, user_name):
        self.connections[user_name] = {
            'latency': deque(maxlen=self.window_size),
            'packet_loss': deque(maxlen=self.window_size),
            'jitter': deque(maxlen=self.window_size)
        }
    
    def update_metrics(self, user_name, latency, packet_received):
        if user_name not in self.connections:
            return
            
        conn = self.connections[user_name]
        
        # Update latency
        conn['latency'].append(latency)
        
        # Calculate jitter
        if len(conn['latency']) >= 2:
            jitter = abs(conn['latency'][-1] - conn['latency'][-2])
            conn['jitter'].append(jitter)
        
        # Update packet loss
        conn['packet_loss'].append(0 if packet_received else 1)
        
        # Calculate metrics
        metrics = {
            'avg_latency': statistics.mean(conn['latency']),
            'jitter': statistics.mean(conn['jitter']) if conn['jitter'] else 0,
            'packet_loss': (sum(conn['packet_loss']) / len(conn['packet_loss'])) * 100
        }
        
        self.quality_updated.emit(user_name, metrics)
