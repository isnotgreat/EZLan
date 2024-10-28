from sklearn.ensemble import RandomForestClassifier
import numpy as np
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class NetworkCondition:
    latency: float
    bandwidth: float
    packet_loss: float
    jitter: float
    connection_stability: float

class MLStrategySelector:
    def __init__(self):
        self.model = RandomForestClassifier()
        self.training_data = []
        self.training_labels = []
        
    def add_training_sample(self, conditions: NetworkCondition, 
                          strategy: str, performance_score: float):
        features = [
            conditions.latency,
            conditions.bandwidth,
            conditions.packet_loss,
            conditions.jitter,
            conditions.connection_stability
        ]
        self.training_data.append(features)
        self.training_labels.append(strategy)
        
        if len(self.training_data) >= 50:  # Train after collecting enough samples
            self.train_model()
            
    def train_model(self):
        X = np.array(self.training_data)
        y = np.array(self.training_labels)
        self.model.fit(X, y)
        
    def suggest_strategy(self, conditions: NetworkCondition) -> str:
        if len(self.training_data) < 50:
            return "balanced"  # Default strategy
            
        features = [
            conditions.latency,
            conditions.bandwidth,
            conditions.packet_loss,
            conditions.jitter,
            conditions.connection_stability
        ]
        return self.model.predict([features])[0]
