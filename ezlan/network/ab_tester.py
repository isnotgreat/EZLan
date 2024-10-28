from dataclasses import dataclass
import numpy as np
from typing import Dict, List
import time

@dataclass
class ABTestResult:
    variant_a: dict
    variant_b: dict
    winner: str
    improvement: float
    confidence: float
    metrics: dict

class ABTester:
    def __init__(self, tunnel_service):
        self.tunnel_service = tunnel_service
        self.test_duration = 60  # 1 minute per variant
        self.current_tests = {}
        
    async def run_test(self, user_name, variant_a, variant_b):
        metrics_a = await self._test_variant(user_name, variant_a)
        metrics_b = await self._test_variant(user_name, variant_b)
        
        # Calculate statistical significance
        confidence = self._calculate_confidence(metrics_a, metrics_b)
        
        # Determine winner
        score_a = self._calculate_score(metrics_a)
        score_b = self._calculate_score(metrics_b)
        
        winner = 'A' if score_a > score_b else 'B'
        improvement = abs(score_a - score_b) / min(score_a, score_b)
        
        return ABTestResult(
            variant_a=variant_a,
            variant_b=variant_b,
            winner=winner,
            improvement=improvement,
            confidence=confidence,
            metrics={'A': metrics_a, 'B': metrics_b}
        )
