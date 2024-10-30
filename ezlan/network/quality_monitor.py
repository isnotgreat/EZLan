from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from ezlan.utils.logger import Logger

class QualityMonitor(QObject):
    quality_updated = pyqtSignal(str, float)  # user, quality_score
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("QualityMonitor")
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 1.0  # 1 second update interval
        
    def start(self):
        """Start quality monitoring"""
        try:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Quality monitoring started")
        except Exception as e:
            self.logger.error(f"Failed to start quality monitoring: {e}")
            raise
            
    def stop(self):
        """Stop quality monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Quality monitoring stopped")
        
    def add_connection(self, user_name):
        """Add a connection to monitor"""
        with self._lock:
            self.connections[user_name] = {
                'latency': [],
                'packet_loss': [],
                'jitter': [],
                'last_update': time.time()
            }
            
    def update_metrics(self, user_name, latency, packet_loss, jitter):
        """Update quality metrics for a connection"""
        with self._lock:
            if user_name in self.connections:
                conn = self.connections[user_name]
                conn['latency'].append(latency)
                conn['packet_loss'].append(packet_loss)
                conn['jitter'].append(jitter)
                conn['last_update'] = time.time()
                
                # Keep only last 10 measurements
                if len(conn['latency']) > 10:
                    conn['latency'] = conn['latency'][-10:]
                    conn['packet_loss'] = conn['packet_loss'][-10:]
                    conn['jitter'] = conn['jitter'][-10:]
                    
                # Calculate quality score
                quality_score = self._calculate_quality(conn)
                self.quality_updated.emit(user_name, quality_score)
                
    def _calculate_quality(self, metrics):
        """Calculate overall quality score from metrics"""
        try:
            # Get average values
            avg_latency = sum(metrics['latency']) / len(metrics['latency'])
            avg_packet_loss = sum(metrics['packet_loss']) / len(metrics['packet_loss'])
            avg_jitter = sum(metrics['jitter']) / len(metrics['jitter'])
            
            # Calculate individual scores (0-1 range)
            latency_score = max(0, 1 - (avg_latency / 200))  # Up to 200ms latency
            packet_loss_score = max(0, 1 - (avg_packet_loss * 20))  # Up to 5% loss
            jitter_score = max(0, 1 - (avg_jitter / 50))  # Up to 50ms jitter
            
            # Weighted average
            quality_score = (
                latency_score * 0.4 +
                packet_loss_score * 0.4 +
                jitter_score * 0.2
            )
            
            return max(0, min(1, quality_score))  # Ensure result is between 0 and 1
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0
            
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    # Check for stale connections
                    for user_name, conn in list(self.connections.items()):
                        if now - conn['last_update'] > 10.0:  # 10 second timeout
                            self.logger.warning(f"Connection {user_name} timed out")
                            del self.connections[user_name]
                            
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
