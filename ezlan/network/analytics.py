from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
from typing import Dict, Optional
import time
import threading
from ezlan.utils.logger import Logger

@dataclass
class NetworkMetrics:
    avg_latency: float = 0.0
    packet_loss: float = 0.0
    bandwidth_utilization: float = 0.0
    jitter: float = 0.0
    connection_quality: float = 1.0
    timestamp: float = 0.0

class NetworkAnalytics(QObject):
    metrics_updated = pyqtSignal(str, object)  # username, metrics
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("NetworkAnalytics")
        self.active_connections: Dict[str, NetworkMetrics] = {}
        self.running = False
        self.update_interval = 1.0  # 1 second update interval
        self._lock = threading.Lock()
        
    def start(self):
        """Start the analytics service"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("Network analytics service started")
        
    def stop(self):
        """Stop the analytics service"""
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join(timeout=2.0)
        self.logger.info("Network analytics service stopped")
        
    def add_connection(self, username: str):
        """Add a new connection to monitor"""
        with self._lock:
            if username not in self.active_connections:
                self.active_connections[username] = NetworkMetrics(timestamp=time.time())
                self.logger.info(f"Started monitoring connection: {username}")
                
    def remove_connection(self, username: str):
        """Remove a connection from monitoring"""
        with self._lock:
            if username in self.active_connections:
                del self.active_connections[username]
                self.logger.info(f"Stopped monitoring connection: {username}")
                
    def update_metrics(self, username: str, metrics: NetworkMetrics):
        """Update metrics for a connection"""
        with self._lock:
            if username in self.active_connections:
                metrics.timestamp = time.time()
                self.active_connections[username] = metrics
                self.metrics_updated.emit(username, metrics)
                
    def get_current_metrics(self, username: str) -> Optional[NetworkMetrics]:
        """Get current metrics for a connection"""
        with self._lock:
            return self.active_connections.get(username)
            
    def _update_loop(self):
        """Background loop to update metrics"""
        while self.running:
            try:
                current_time = time.time()
                with self._lock:
                    # Update metrics for each connection
                    for username, metrics in list(self.active_connections.items()):
                        if current_time - metrics.timestamp > 10.0:  # 10 second timeout
                            self.logger.warning(f"Connection timeout for {username}")
                            self.remove_connection(username)
                            continue
                            
                        # Calculate connection quality based on metrics
                        quality = self._calculate_quality(metrics)
                        metrics.connection_quality = quality
                        self.metrics_updated.emit(username, metrics)
                        
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
                
    def _calculate_quality(self, metrics: NetworkMetrics) -> float:
        """Calculate overall connection quality score"""
        try:
            # Normalize metrics to 0-1 range
            latency_score = max(0, 1 - (metrics.avg_latency / 200))  # Up to 200ms latency
            packet_loss_score = max(0, 1 - (metrics.packet_loss * 20))  # Up to 5% loss
            bandwidth_score = min(1, metrics.bandwidth_utilization / (1024 * 1024))  # Up to 1MB/s
            jitter_score = max(0, 1 - (metrics.jitter / 50))  # Up to 50ms jitter
            
            # Weighted average of scores
            quality = (
                latency_score * 0.4 +
                packet_loss_score * 0.3 +
                bandwidth_score * 0.2 +
                jitter_score * 0.1
            )
            
            return max(0, min(1, quality))  # Ensure result is between 0 and 1
            
        except Exception as e:
            self.logger.error(f"Error calculating quality: {e}")
            return 0.0
