from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from ezlan.utils.logger import Logger

class ConnectionRecoveryManager(QObject):
    recovery_started = pyqtSignal(str)  # user_name
    recovery_succeeded = pyqtSignal(str)  # user_name
    recovery_failed = pyqtSignal(str, str)  # user_name, error_message
    
    def __init__(self, tunnel_service):
        super().__init__()
        self.logger = Logger("ConnectionRecoveryManager")
        self.tunnel_service = tunnel_service
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 5.0  # 5 second check interval
        self.max_retries = 3
        
    def start(self):
        """Start connection recovery monitoring"""
        try:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Connection recovery monitoring started")
        except Exception as e:
            self.logger.error(f"Failed to start connection recovery: {e}")
            raise
            
    def stop(self):
        """Stop connection recovery monitoring"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Connection recovery monitoring stopped")
        
    def add_connection(self, user_name):
        """Add a connection to monitor"""
        with self._lock:
            self.connections[user_name] = {
                'last_check': time.time(),
                'retry_count': 0,
                'recovering': False
            }
            
    def _monitor_loop(self):
        """Background loop for connection monitoring"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    for user_name, conn in list(self.connections.items()):
                        # Check connection health
                        if self._needs_recovery(user_name):
                            self._attempt_recovery(user_name)
                            
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
                
    def _needs_recovery(self, user_name):
        """Check if connection needs recovery"""
        try:
            if user_name not in self.tunnel_service.active_tunnels:
                return False
                
            metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
            if not metrics:
                return True
                
            # Check for severe issues
            if metrics.packet_loss > 0.5:  # >50% packet loss
                return True
                
            if metrics.avg_latency > 1000:  # >1s latency
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking connection health: {e}")
            return False
            
    def _attempt_recovery(self, user_name):
        """Attempt to recover connection"""
        try:
            conn = self.connections[user_name]
            
            # Check retry limit
            if conn['retry_count'] >= self.max_retries:
                self.logger.warning(f"Max retries reached for {user_name}")
                self.recovery_failed.emit(user_name, "Max retries exceeded")
                return
                
            if not conn['recovering']:
                conn['recovering'] = True
                self.recovery_started.emit(user_name)
                
                # Increment retry count
                conn['retry_count'] += 1
                
                # Get connection info
                tunnel = self.tunnel_service.active_tunnels.get(user_name)
                if not tunnel:
                    return
                    
                # Try to reconnect
                if self._reconnect(user_name, tunnel):
                    conn['recovering'] = False
                    conn['retry_count'] = 0
                    self.recovery_succeeded.emit(user_name)
                else:
                    self.recovery_failed.emit(user_name, "Reconnection failed")
                    
        except Exception as e:
            self.logger.error(f"Error during recovery attempt: {e}")
            self.recovery_failed.emit(user_name, str(e))
            
    def _reconnect(self, user_name, tunnel):
        """Attempt to reconnect to peer"""
        try:
            # Close existing connection
            self.tunnel_service.disconnect_from_peer(user_name)
            time.sleep(1)  # Wait before reconnecting
            
            # Try to reconnect
            if hasattr(tunnel, 'connection_info'):
                self.tunnel_service.connect_to_peer(tunnel.connection_info)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            return False
