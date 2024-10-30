from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
import numpy as np
from typing import Dict, List

@dataclass
class GamingMetrics:
    frame_time: float
    ping_stability: float
    jitter: float
    packet_loss: float

class GamingOptimizer(QObject):
    optimization_applied = pyqtSignal(str, dict)  # user_name, changes
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.optimization_history: Dict[str, List[dict]] = {}
        self.gaming_thresholds = {
            'frame_time': 16.67,  # 60 FPS target
            'ping_stability': 0.95,
            'jitter': 5.0,
            'packet_loss': 0.01
        }
        
    def optimize_for_gaming(self, user_name):
        metrics = self._get_gaming_metrics(user_name)
        if not metrics:
            return False
            
        # Calculate current performance score
        current_score = self._calculate_gaming_score(metrics)
        
        # Get optimization strategy based on current performance
        strategy = self._select_optimization_strategy(metrics)
        
        # Generate and apply optimizations
        changes = self._generate_gaming_optimizations(metrics, strategy)
        if changes:
            self._apply_gaming_optimizations(user_name, changes)
            self.optimization_applied.emit(user_name, changes)
            
        return True
        
    def _calculate_gaming_score(self, metrics: GamingMetrics) -> float:
        # Weight different aspects based on gaming importance
        weights = {
            'frame_time': 0.4,
            'ping_stability': 0.3,
            'jitter': 0.2,
            'packet_loss': 0.1
        }
        
        scores = {
            'frame_time': max(0, 1 - (metrics.frame_time / self.gaming_thresholds['frame_time'])),
            'ping_stability': metrics.ping_stability / self.gaming_thresholds['ping_stability'],
            'jitter': max(0, 1 - (metrics.jitter / self.gaming_thresholds['jitter'])),
            'packet_loss': max(0, 1 - (metrics.packet_loss / self.gaming_thresholds['packet_loss']))
        }
        
        return sum(scores[k] * weights[k] for k in weights)