from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from ezlan.utils.logger import Logger

class AutoOptimizer(QObject):
    optimization_applied = pyqtSignal(str, str)  # user, optimization_description
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.logger = Logger("AutoOptimizer")
        self.tunnel_service = tunnel_service
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 5.0  # 5 second update interval
        
    def start(self):
        """Start auto optimization"""
        try:
            self.running = True
            self.optimizer_thread = threading.Thread(target=self._optimizer_loop, daemon=True)
            self.optimizer_thread.start()
            self.logger.info("Auto optimization started")
        except Exception as e:
            self.logger.error(f"Failed to start auto optimization: {e}")
            raise
            
    def stop(self):
        """Stop auto optimization"""
        self.running = False
        if hasattr(self, 'optimizer_thread'):
            self.optimizer_thread.join(timeout=2.0)
        self.logger.info("Auto optimization stopped")
        
    def add_connection(self, user_name):
        """Add a connection to optimize"""
        with self._lock:
            self.connections[user_name] = {
                'last_optimization': time.time(),
                'optimizations_applied': []
            }
            
    def _optimizer_loop(self):
        """Background loop for auto optimization"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    for user_name, conn in list(self.connections.items()):
                        # Check if enough time has passed since last optimization
                        if now - conn['last_optimization'] > 30:  # 30 second cooldown
                            self._optimize_connection(user_name)
                            conn['last_optimization'] = now
                            
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in optimizer loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
                
    def _optimize_connection(self, user_name):
        """Apply optimizations for a connection"""
        try:
            # Get current metrics
            metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
            if not metrics:
                return
                
            optimizations = []
            
            # Check latency
            if metrics.avg_latency > 100:  # High latency
                self._apply_latency_optimization(user_name)
                optimizations.append("Latency optimization")
                
            # Check packet loss
            if metrics.packet_loss > 0.02:  # >2% packet loss
                self._apply_reliability_optimization(user_name)
                optimizations.append("Reliability optimization")
                
            # Check bandwidth
            if metrics.bandwidth_utilization < 500000:  # <500KB/s
                self._apply_bandwidth_optimization(user_name)
                optimizations.append("Bandwidth optimization")
                
            if optimizations:
                self.optimization_applied.emit(user_name, ", ".join(optimizations))
                
        except Exception as e:
            self.logger.error(f"Error optimizing connection: {e}")
            
    def _apply_latency_optimization(self, user_name):
        """Apply optimizations for high latency"""
        try:
            # Update QoS policy
            policy = self.tunnel_service.traffic_shaper.policies.get(user_name)
            if policy:
                policy.priority = max(policy.priority, 6)  # Increase priority
                policy.latency_target = 50  # Set target latency to 50ms
                self.tunnel_service.traffic_shaper.update_policy(user_name, policy)
                
        except Exception as e:
            self.logger.error(f"Error applying latency optimization: {e}")
            
    def _apply_reliability_optimization(self, user_name):
        """Apply optimizations for packet loss"""
        try:
            # Enable packet retransmission
            if user_name in self.tunnel_service.active_tunnels:
                tunnel = self.tunnel_service.active_tunnels[user_name]
                if hasattr(tunnel, 'enable_retransmission'):
                    tunnel.enable_retransmission()
                    
        except Exception as e:
            self.logger.error(f"Error applying reliability optimization: {e}")
            
    def _apply_bandwidth_optimization(self, user_name):
        """Apply optimizations for low bandwidth"""
        try:
            # Update bandwidth allocation
            self.tunnel_service.bandwidth_allocator.increase_allocation(
                user_name,
                increment=1024*1024  # Increase by 1MB/s
            )
            
        except Exception as e:
            self.logger.error(f"Error applying bandwidth optimization: {e}")
