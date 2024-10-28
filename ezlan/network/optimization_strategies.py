from enum import Enum
from dataclasses import dataclass
from typing import List, Dict
import numpy as np

class OptimizationStrategy(Enum):
    CONSERVATIVE = "Conservative"
    BALANCED = "Balanced"
    AGGRESSIVE = "Aggressive"
    LEARNING = "Learning Mode"

@dataclass
class StrategyConfig:
    max_change_per_step: float
    measurement_window: int
    confidence_threshold: float
    rollback_threshold: float

class StrategyManager:
    def __init__(self):
        self.strategies = {
            OptimizationStrategy.CONSERVATIVE: StrategyConfig(0.1, 60, 0.9, 0.95),
            OptimizationStrategy.AGGRESSIVE: StrategyConfig(0.3, 30, 0.7, 0.8),
            OptimizationStrategy.BALANCED: StrategyConfig(0.2, 45, 0.8, 0.9),
            OptimizationStrategy.LEARNING: StrategyConfig(0.15, 90, 0.85, 0.92)
        }
        
    def get_next_change(self, strategy: OptimizationStrategy, 
                       current_metrics: dict, history: List[dict]) -> dict:
        config = self.strategies[strategy]
        
        # Calculate trend
        trend = self._calculate_metric_trends(history)
        
        # Generate suggested changes based on strategy
        changes = {}
        for metric, trend_value in trend.items():
            max_change = config.max_change_per_step
            suggested_change = trend_value * max_change
            
            # Apply strategy-specific constraints
            if strategy == OptimizationStrategy.CONSERVATIVE:
                suggested_change *= 0.5
            elif strategy == OptimizationStrategy.AGGRESSIVE:
                suggested_change *= 1.5
                
            changes[metric] = suggested_change
            
        return changes
