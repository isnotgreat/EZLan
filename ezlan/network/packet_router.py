import threading
import struct
from collections import defaultdict

class PacketRouter:
    def __init__(self):
        self.routing_table = defaultdict(set)
        self.lock = threading.Lock()
    
    def add_route(self, source_ip, destination_ip, tunnel):
        with self.lock:
            self.routing_table[destination_ip].add((source_ip, tunnel))
    
    def remove_route(self, source_ip, destination_ip):
        with self.lock:
            if destination_ip in self.routing_table:
                self.routing_table[destination_ip] = {
                    (src, tunnel) for src, tunnel in self.routing_table[destination_ip]
                    if src != source_ip
                }
    
    def route_packet(self, source_ip, destination_ip, packet_data):
        with self.lock:
            if destination_ip in self.routing_table:
                packet_header = struct.pack('!4s4s', 
                    bytes(map(int, source_ip.split('.'))),
                    bytes(map(int, destination_ip.split('.')))
                )
                packet = packet_header + packet_data
                
                for _, tunnel in self.routing_table[destination_ip]:
                    try:
                        tunnel.send(packet)
                    except Exception as e:
                        print(f"Failed to route packet: {e}")
