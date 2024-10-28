from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
import time

@dataclass
class PerformanceMetrics:
    avg_latency: float
    jitter: float
    packet_loss: float
    bandwidth_utilization: float
    connection_stability: float  # 0-1 score

class NetworkAnalytics(QObject):
    metrics_updated = pyqtSignal(str, PerformanceMetrics)
    alert_triggered = pyqtSignal(str, str)  # user_name, alert_message
    
    def __init__(self):
        super().__init__()
        self.metrics_history: Dict[str, Dict[str, List[float]]] = {}
        self.analysis_window = 60  # 60 seconds of history
        
    def add_connection(self, user_name):
        self.metrics_history[user_name] = {
            'latency': [],
            'jitter': [],
            'packet_loss': [],
            'bandwidth': []
        }
        
    def update_metrics(self, user_name, latency, jitter, packet_loss, bandwidth):
        if user_name not in self.metrics_history:
            self.add_connection(user_name)
            
        history = self.metrics_history[user_name]
        current_time = time.time()
        
        # Update history
        history['latency'].append(latency)
        history['jitter'].append(jitter)
        history['packet_loss'].append(packet_loss)
        history['bandwidth'].append(bandwidth)
        
        # Trim old data
        for metric in history.values():
            if len(metric) > self.analysis_window:
                metric.pop(0)
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(history)
        self.metrics_updated.emit(user_name, metrics)
        
        # Check for performance issues
        self._check_alerts(user_name, metrics)
    
    def _calculate_metrics(self, history) -> PerformanceMetrics:
        avg_latency = np.mean(history['latency'])
        jitter = np.std(history['latency'])
        packet_loss = np.mean(history['packet_loss'])
        bandwidth_util = np.mean(history['bandwidth'])
        
        # Calculate connection stability score
        stability = 1.0
        if avg_latency > 100:  # High latency penalty
            stability *= 0.8
        if jitter > 20:  # High jitter penalty
            stability *= 0.7
        if packet_loss > 0.02:  # Packet loss penalty
            stability *= 0.6
            
        return PerformanceMetrics(
            avg_latency=avg_latency,
            jitter=jitter,
            packet_loss=packet_loss,
            bandwidth_utilization=bandwidth_util,
            connection_stability=stability
        )
