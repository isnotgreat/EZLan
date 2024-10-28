from sklearn.ensemble import RandomForestRegressor
import numpy as np
from dataclasses import dataclass
from typing import Dict, List
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class OptimizationSuggestion:
    parameter: str
    current_value: float
    suggested_value: float
    confidence: float
    impact: str

class PredictiveOptimizer(QObject):
    optimization_suggested = pyqtSignal(str, OptimizationSuggestion)
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.models = {}
        self.training_data = {}
        self.min_samples = 30
        
    def add_connection(self, user_name):
        self.training_data[user_name] = {
            'features': [],
            'targets': []
        }
        self.models[user_name] = {
            'latency': RandomForestRegressor(),
            'packet_loss': RandomForestRegressor(),
            'bandwidth': RandomForestRegressor()
        }
        
    def update_training_data(self, user_name, metrics, qos_settings):
        if user_name not in self.training_data:
            self.add_connection(user_name)
            
        # Extract features from QoS settings and current metrics
        features = [
            qos_settings.priority,
            qos_settings.bandwidth_limit,
            qos_settings.latency_target,
            metrics.avg_latency,
            metrics.jitter,
            metrics.packet_loss,
            metrics.bandwidth_utilization
        ]
        
        self.training_data[user_name]['features'].append(features)
        self.training_data[user_name]['targets'].append([
            metrics.avg_latency,
            metrics.packet_loss,
            metrics.bandwidth_utilization
        ])
        
        # Train models if enough data is available
        if len(self.training_data[user_name]['features']) >= self.min_samples:
            self.train_models(user_name)
            self.suggest_optimizations(user_name)
            
    def train_models(self, user_name):
        X = np.array(self.training_data[user_name]['features'])
        y = np.array(self.training_data[user_name]['targets'])
        
        for i, metric in enumerate(['latency', 'packet_loss', 'bandwidth']):
            self.models[user_name][metric].fit(X, y[:, i])
            
    def suggest_optimizations(self, user_name):
        current_metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
        current_qos = self.tunnel_service.traffic_shaper.get_policy(user_name)
        
        # Test different parameter combinations
        best_suggestion = None
        best_improvement = 0
        
        for priority in range(1, 10):
            for bw_limit in range(512, 5120, 512):  # 512KB/s to 5MB/s
                for latency_target in range(20, 200, 20):
                    suggestion = self.evaluate_parameters(
                        user_name, priority, bw_limit, latency_target,
                        current_metrics, current_qos
                    )
                    
                    if suggestion and suggestion.confidence > best_improvement:
                        best_suggestion = suggestion
                        best_improvement = suggestion.confidence
        
        if best_suggestion:
            self.optimization_suggested.emit(user_name, best_suggestion)
