from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class BandwidthAllocation:
    guaranteed_bandwidth: int  # bytes/s
    burst_bandwidth: int      # bytes/s
    weight: float            # 0-1 priority weight

class BandwidthAllocator(QObject):
    allocation_updated = pyqtSignal(str, BandwidthAllocation)
    
    def __init__(self, total_bandwidth):
        super().__init__()
        self.total_bandwidth = total_bandwidth
        self.allocations: Dict[str, BandwidthAllocation] = {}
        self.usage_history: Dict[str, List[float]] = {}
        
    def add_connection(self, user_name, initial_weight=0.5):
        self.allocations[user_name] = BandwidthAllocation(
            guaranteed_bandwidth=int(self.total_bandwidth * 0.2),
            burst_bandwidth=int(self.total_bandwidth * 0.8),
            weight=initial_weight
        )
        self.usage_history[user_name] = []
        
    def update_allocation(self):
        if not self.allocations:
            return
            
        total_weight = sum(alloc.weight for alloc in self.allocations.values())
        available_bandwidth = self.total_bandwidth
        
        # Calculate fair share based on weights and usage history
        for user_name, allocation in self.allocations.items():
            usage = np.mean(self.usage_history[user_name][-10:]) if self.usage_history[user_name] else 0
            fair_share = (allocation.weight / total_weight) * available_bandwidth
            
            # Adjust based on historical usage
            if usage < fair_share * 0.8:
                allocation.weight *= 1.1  # Increase weight if underutilizing
            elif usage > fair_share * 0.9:
                allocation.weight *= 0.9  # Decrease weight if over-utilizing
                
            # Update allocation
            new_allocation = BandwidthAllocation(
                guaranteed_bandwidth=int(fair_share * 0.2),
                burst_bandwidth=int(fair_share * 0.8),
                weight=allocation.weight
            )
            self.allocations[user_name] = new_allocation
            self.allocation_updated.emit(user_name, new_allocation)
