from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
import numpy as np
import time

@dataclass
class GamingMetrics:
    frame_time: float
    frame_time_variance: float
    network_stability: float
    optimization_score: float

class GamingPerformanceMonitor(QObject):
    metrics_updated = pyqtSignal(str, GamingMetrics)
    performance_alert = pyqtSignal(str, str)
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.metrics_history = {}
        self.window_size = 60
        self._setup_monitoring()
        
    def _setup_monitoring(self):
        # Connect to existing monitoring signals
        self.tunnel_service.quality_monitor.quality_updated.connect(self._on_quality_update)
        self.tunnel_service.network_analytics.metrics_updated.connect(self._on_analytics_update)