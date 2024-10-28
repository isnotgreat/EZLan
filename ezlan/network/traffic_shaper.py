from PyQt6.QtCore import QObject, pyqtSignal
import time
import threading
from collections import deque
from queue import PriorityQueue

class QoSPolicy:
    def __init__(self, priority=0, bandwidth_limit=None, latency_target=None):
        self.priority = priority  # 0-9, higher is more important
        self.bandwidth_limit = bandwidth_limit  # bytes per second
        self.latency_target = latency_target  # milliseconds

class TrafficShaper(QObject):
    bandwidth_limited = pyqtSignal(str)  # user_name
    
    def __init__(self):
        super().__init__()
        self.packet_queues = {}
        self.policies = {}
        self.running = True
        
    def add_connection(self, user_name, policy=None):
        if policy is None:
            policy = QoSPolicy()
        self.policies[user_name] = policy
        self.packet_queues[user_name] = PriorityQueue()
        
        # Start processing thread for this connection
        threading.Thread(
            target=self._process_queue,
            args=(user_name,),
            daemon=True
        ).start()
    
    def enqueue_packet(self, user_name, packet, priority_override=None):
        if user_name in self.packet_queues:
            priority = (
                priority_override 
                if priority_override is not None 
                else self.policies[user_name].priority
            )
            self.packet_queues[user_name].put((-priority, time.time(), packet))
    
    def _process_queue(self, user_name):
        last_send_time = time.time()
        bytes_sent = 0
        
        while self.running and user_name in self.packet_queues:
            try:
                policy = self.policies[user_name]
                queue = self.packet_queues[user_name]
                
                if not queue.empty():
                    _, timestamp, packet = queue.get()
                    packet_size = len(packet)
                    
                    # Apply bandwidth limiting
                    if policy.bandwidth_limit:
                        current_time = time.time()
                        time_diff = current_time - last_send_time
                        
                        if bytes_sent + packet_size > policy.bandwidth_limit * time_diff:
                            self.bandwidth_limited.emit(user_name)
                            time.sleep(0.1)
                            continue
                        
                        bytes_sent += packet_size
                        
                    # Apply latency target if specified
                    if policy.latency_target:
                        packet_age = (time.time() - timestamp) * 1000
                        if packet_age > policy.latency_target:
                            continue
                    
                    yield packet
                    last_send_time = time.time()
                    
            except Exception as e:
                print(f"Error processing packet queue: {e}")
                time.sleep(0.1)
