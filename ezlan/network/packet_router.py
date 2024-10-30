import socket
import threading
from ezlan.utils.logger import Logger

class PacketRouter:
    def __init__(self):
        self.logger = Logger("PacketRouter")
        self.routing_table = {}  # Maps IP ranges to destinations
        self._lock = threading.Lock()
        
    def add_route(self, source_ip, dest_network, destination):
        """Add a route to the routing table"""
        with self._lock:
            self.routing_table[dest_network] = {
                'source_ip': source_ip,
                'destination': destination
            }
            self.logger.info(f"Added route from {source_ip} to {dest_network}")
            
    def remove_route(self, dest_network):
        """Remove a route from the routing table"""
        with self._lock:
            if dest_network in self.routing_table:
                del self.routing_table[dest_network]
                self.logger.info(f"Removed route to {dest_network}")
                
    def route_packet(self, source_ip, dest_ip, packet):
        """Route a packet to its destination"""
        try:
            with self._lock:
                # Find matching route
                for network, route in self.routing_table.items():
                    if self._ip_in_network(dest_ip, network):
                        destination = route['destination']
                        if isinstance(destination, socket.socket):
                            destination.send(packet)
                        else:
                            destination.write_packet(packet)
                        return True
                        
            # No route found
            self.logger.debug(f"No route found for packet from {source_ip} to {dest_ip}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error routing packet: {e}")
            return False
            
    def _ip_in_network(self, ip, network):
        """Check if IP is in network range"""
        try:
            # Simple string comparison for now
            # Could be enhanced with proper IP address handling
            return ip.startswith(network.split('.')[0])
        except:
            return False
            
    def clear(self):
        """Clear all routes"""
        with self._lock:
            self.routing_table.clear()
            self.logger.info("Cleared all routes")
