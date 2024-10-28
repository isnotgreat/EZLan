from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class OptimizationResult:
    success: bool
    metrics_before: dict
    metrics_after: dict
    changes_made: dict
    improvement: float

class AutoOptimizer(QObject):
    optimization_started = pyqtSignal(str)  # user_name
    optimization_complete = pyqtSignal(str, OptimizationResult)
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.optimization_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, bool] = {}
        
    def start_optimization(self, user_name):
        if user_name in self.optimization_threads and self.optimization_threads[user_name].is_alive():
            return False
            
        self.stop_flags[user_name] = False
        self.optimization_started.emit(user_name)
        
        thread = threading.Thread(
            target=self._optimization_loop,
            args=(user_name,),
            daemon=True
        )
        self.optimization_threads[user_name] = thread
        thread.start()
        return True
        
    def stop_optimization(self, user_name):
        if user_name in self.stop_flags:
            self.stop_flags[user_name] = True
            
    def _optimization_loop(self, user_name):
        metrics_before = self.tunnel_service.network_analytics.get_current_metrics(user_name)
        changes_made = {}
        best_score = self._calculate_performance_score(metrics_before)
        
        while not self.stop_flags.get(user_name, True):
            # Get optimization suggestion
            suggestion = self.tunnel_service.predictive_optimizer.get_suggestion(user_name)
            
            if suggestion and suggestion.confidence > 0.7:  # Only apply high-confidence changes
                # Apply suggested changes
                current_policy = self.tunnel_service.traffic_shaper.get_policy(user_name)
                new_policy = self._apply_suggestion(current_policy, suggestion)
                
                # Test the changes
                self.tunnel_service.update_qos_policy(user_name, new_policy)
                time.sleep(10)  # Wait for effects to stabilize
                
                # Evaluate results
                current_metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
                new_score = self._calculate_performance_score(current_metrics)
                
                if new_score > best_score:
                    best_score = new_score
                    changes_made[suggestion.parameter] = suggestion.suggested_value
                else:
                    # Revert changes if no improvement
                    self.tunnel_service.update_qos_policy(user_name, current_policy)
            
            time.sleep(30)  # Wait before next optimization attempt
            
        # Calculate final results
        metrics_after = self.tunnel_service.network_analytics.get_current_metrics(user_name)
        improvement = (best_score - self._calculate_performance_score(metrics_before)) / best_score
        
        result = OptimizationResult(
            success=bool(changes_made),
            metrics_before=vars(metrics_before),
            metrics_after=vars(metrics_after),
            changes_made=changes_made,
            improvement=improvement
        )
        
        self.optimization_complete.emit(user_name, result)
        
    def _calculate_performance_score(self, metrics):
        # Weight different metrics based on importance
        latency_score = max(0, 1 - (metrics.avg_latency / 200))
        packet_loss_score = max(0, 1 - (metrics.packet_loss * 20))
        bandwidth_score = min(1, metrics.bandwidth_utilization / (1024 * 1024))
        stability_score = metrics.connection_stability
        
        return (
            latency_score * 0.3 +
            packet_loss_score * 0.3 +
            bandwidth_score * 0.2 +
            stability_score * 0.2
        )
        
    def _apply_suggestion(self, current_policy, suggestion):
        new_policy = current_policy.copy()
        setattr(new_policy, suggestion.parameter, suggestion.suggested_value)
        return new_policy
