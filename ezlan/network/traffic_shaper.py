from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from collections import deque
from dataclasses import dataclass
from ezlan.utils.logger import Logger

@dataclass
class QoSPolicy:
    priority: int = 0  # 0-7, higher is more important
    bandwidth_limit: int = 0  # bytes per second, 0 for unlimited
    latency_target: float = 0.0  # target latency in ms, 0 for best effort

class TrafficShaper(QObject):
    shaping_updated = pyqtSignal(str, float)  # user, bandwidth_usage
    
    def __init__(self):
        super().__init__()
        self.logger = Logger("TrafficShaper")
        self.running = False
        self.connections = {}
        self._lock = threading.Lock()
        self.update_interval = 0.1  # 100ms update interval
        self.packet_queues = {}
        self.policies = {}
        
    def start(self):
        """Start traffic shaping"""
        try:
            self.running = True
            self.shaper_thread = threading.Thread(target=self._shaper_loop, daemon=True)
            self.shaper_thread.start()
            self.logger.info("Traffic shaping started")
        except Exception as e:
            self.logger.error(f"Failed to start traffic shaping: {e}")
            raise
            
    def stop(self):
        """Stop traffic shaping"""
        self.running = False
        if hasattr(self, 'shaper_thread'):
            self.shaper_thread.join(timeout=2.0)
        self.logger.info("Traffic shaping stopped")
        
    def add_connection(self, user_name, policy: QoSPolicy = None):
        """Add a connection with optional QoS policy"""
        with self._lock:
            self.connections[user_name] = {
                'bytes_sent': 0,
                'last_update': time.time(),
                'bandwidth_usage': 0.0
            }
            self.packet_queues[user_name] = deque()
            self.policies[user_name] = policy or QoSPolicy()
            
    def update_policy(self, user_name, policy: QoSPolicy):
        """Update QoS policy for a connection"""
        with self._lock:
            if user_name in self.policies:
                self.policies[user_name] = policy
                
    def enqueue_packet(self, user_name, packet):
        """Add packet to user's queue"""
        with self._lock:
            if user_name in self.packet_queues:
                self.packet_queues[user_name].append((time.time(), packet))
                
    def _process_queue(self, user_name):
        """Process packets in queue according to QoS policy"""
        with self._lock:
            if user_name not in self.packet_queues:
                return []
                
            queue = self.packet_queues[user_name]
            policy = self.policies[user_name]
            now = time.time()
            processed_packets = []
            
            while queue:
                timestamp, packet = queue[0]
                
                # Check bandwidth limit
                if policy.bandwidth_limit > 0:
                    conn = self.connections[user_name]
                    if conn['bandwidth_usage'] >= policy.bandwidth_limit:
                        break
                        
                # Check latency target
                if policy.latency_target > 0:
                    latency = (now - timestamp) * 1000  # Convert to ms
                    if latency > policy.latency_target:
                        # Packet is too old, drop it
                        queue.popleft()
                        continue
                        
                # Process packet
                packet_data = queue.popleft()[1]
                processed_packets.append(packet_data)
                
                # Update bandwidth usage
                if user_name in self.connections:
                    conn = self.connections[user_name]
                    conn['bytes_sent'] += len(packet_data)
                    elapsed = now - conn['last_update']
                    if elapsed > 0:
                        conn['bandwidth_usage'] = conn['bytes_sent'] / elapsed
                        conn['last_update'] = now
                        conn['bytes_sent'] = 0
                        self.shaping_updated.emit(user_name, conn['bandwidth_usage'])
                        
            return processed_packets
            
    def _shaper_loop(self):
        """Background loop for traffic shaping"""
        while self.running:
            try:
                with self._lock:
                    now = time.time()
                    # Process each connection's queue
                    for user_name in list(self.connections.keys()):
                        self._process_queue(user_name)
                        
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in shaper loop: {e}")
                time.sleep(1.0)  # Prevent tight loop on error
