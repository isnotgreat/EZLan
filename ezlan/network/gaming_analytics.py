from dataclasses import dataclass
from typing import List, Dict
import numpy as np

@dataclass
class GamingPerformanceMetrics:
    frame_times: List[float]
    network_stability: float
    optimization_score: float
    latency_consistency: float
    
class GamingAnalytics:
    def __init__(self, network_analytics):
        self.network_analytics = network_analytics
        self.gaming_history: Dict[str, List[GamingPerformanceMetrics]] = {}
        self.analysis_window = 120  # 2 minutes of history
        
    def analyze_gaming_performance(self, user_name) -> GamingPerformanceMetrics:
        metrics = self.network_analytics.get_current_metrics(user_name)
        
        frame_times = self._calculate_frame_times(metrics.latency_history)
        stability = self._calculate_network_stability(metrics)
        optimization = self._calculate_optimization_score(metrics)
        consistency = self._calculate_latency_consistency(metrics.latency_history)
        
        return GamingPerformanceMetrics(
            frame_times=frame_times,
            network_stability=stability,
            optimization_score=optimization,
            latency_consistency=consistency
        )
