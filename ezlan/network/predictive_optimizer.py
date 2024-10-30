from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
import numpy as np
from ezlan.utils.logger import Logger

class PredictiveOptimizer(QObject):
    prediction_made = pyqtSignal(str, str)  # user, prediction_description
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.logger = Logger("PredictiveOptimizer")
        self.tunnel_service = tunnel_service
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 10.0  # 10 second update interval
        self.history_length = 60  # Keep 60 data points
        
    def start(self):
        """Start predictive optimization"""
        try:
            self.running = True
            self.optimizer_thread = threading.Thread(target=self._optimizer_loop, daemon=True)
            self.optimizer_thread.start()
            self.logger.info("Predictive optimization started")
        except Exception as e:
            self.logger.error(f"Failed to start predictive optimization: {e}")
            raise
            
    def stop(self):
        """Stop predictive optimization"""
        self.running = False
        if hasattr(self, 'optimizer_thread'):
            self.optimizer_thread.join(timeout=2.0)
        self.logger.info("Predictive optimization stopped")
        
    def add_connection(self, user_name):
        """Add a connection to monitor"""
        with self._lock:
            self.connections[user_name] = {
                'latency_history': [],
                'packet_loss_history': [],
                'bandwidth_history': [],
                'last_update': time.time(),
                'predictions': {}
            }
            
    def _optimizer_loop(self):
        """Background loop for predictive optimization"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    for user_name, conn in list(self.connections.items()):
                        # Update metrics history
                        self._update_metrics_history(user_name)
                        # Make predictions
                        self._make_predictions(user_name)
                        
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimizer loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
                
    def _update_metrics_history(self, user_name):
        """Update metrics history for a connection"""
        try:
            metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
            if not metrics:
                return
                
            conn = self.connections[user_name]
            
            # Add new metrics to history
            conn['latency_history'].append(metrics.avg_latency)
            conn['packet_loss_history'].append(metrics.packet_loss)
            conn['bandwidth_history'].append(metrics.bandwidth_utilization)
            
            # Keep only last N points
            if len(conn['latency_history']) > self.history_length:
                conn['latency_history'] = conn['latency_history'][-self.history_length:]
                conn['packet_loss_history'] = conn['packet_loss_history'][-self.history_length:]
                conn['bandwidth_history'] = conn['bandwidth_history'][-self.history_length:]
                
        except Exception as e:
            self.logger.error(f"Error updating metrics history: {e}")
            
    def _make_predictions(self, user_name):
        """Make predictions based on historical data"""
        try:
            conn = self.connections[user_name]
            if len(conn['latency_history']) < 10:  # Need at least 10 points
                return
                
            # Simple trend analysis
            latency_trend = np.polyfit(
                range(len(conn['latency_history'])), 
                conn['latency_history'], 
                1
            )[0]
            
            packet_loss_trend = np.polyfit(
                range(len(conn['packet_loss_history'])), 
                conn['packet_loss_history'], 
                1
            )[0]
            
            # Make predictions
            predictions = []
            
            if latency_trend > 0.5:  # Latency increasing
                predictions.append("Latency likely to increase")
                self._apply_preemptive_optimization(user_name, 'latency')
                
            if packet_loss_trend > 0.01:  # Packet loss increasing
                predictions.append("Packet loss likely to increase")
                self._apply_preemptive_optimization(user_name, 'packet_loss')
                
            if predictions:
                self.prediction_made.emit(user_name, ", ".join(predictions))
                
        except Exception as e:
            self.logger.error(f"Error making predictions: {e}")
            
    def _apply_preemptive_optimization(self, user_name, metric_type):
        """Apply preemptive optimizations based on predictions"""
        try:
            if metric_type == 'latency':
                # Update QoS policy preemptively
                policy = self.tunnel_service.traffic_shaper.policies.get(user_name)
                if policy:
                    policy.priority = max(policy.priority, 5)  # Increase priority
                    policy.latency_target = 75  # Set conservative target
                    self.tunnel_service.traffic_shaper.update_policy(user_name, policy)
                    
            elif metric_type == 'packet_loss':
                # Enable more aggressive packet recovery
                if user_name in self.tunnel_service.active_tunnels:
                    tunnel = self.tunnel_service.active_tunnels[user_name]
                    if hasattr(tunnel, 'set_recovery_mode'):
                        tunnel.set_recovery_mode('aggressive')
                        
        except Exception as e:
            self.logger.error(f"Error applying preemptive optimization: {e}")
