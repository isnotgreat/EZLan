from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from datetime import datetime, timedelta

@dataclass
class PerformanceSnapshot:
    timestamp: datetime
    metrics: Dict[str, float]
    strategy: str
    score: float

class PerformanceHistory:
    def __init__(self):
        self.history: List[PerformanceSnapshot] = []
        self.baseline_metrics: Dict[str, float] = {}
        
    def add_snapshot(self, metrics: Dict[str, float], strategy: str, score: float):
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            metrics=metrics.copy(),
            strategy=strategy,
            score=score
        )
        self.history.append(snapshot)
        
        # Update baseline if needed
        if not self.baseline_metrics:
            self.baseline_metrics = metrics.copy()
            
    def get_improvement_metrics(self) -> Dict[str, float]:
        if not self.history:
            return {}
            
        latest = self.history[-1].metrics
        return {
            metric: ((latest[metric] - self.baseline_metrics[metric]) 
                    / self.baseline_metrics[metric] * 100)
            for metric in latest.keys()
        }
