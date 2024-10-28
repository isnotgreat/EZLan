from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import numpy as np
from typing import List, Dict, Tuple

class AdvancedMLSelector:
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3
        )
        self.scaler = StandardScaler()
        self.feature_importance: Dict[str, float] = {}
        
    def train_model(self, features: List[List[float]], labels: List[str]) -> Tuple[float, Dict[str, float]]:
        X = self.scaler.fit_transform(features)
        scores = cross_val_score(self.model, X, labels, cv=5)
        
        self.model.fit(X, labels)
        feature_names = ['latency', 'bandwidth', 'packet_loss', 'jitter', 'stability']
        self.feature_importance = dict(zip(feature_names, self.model.feature_importances_))
        
        return np.mean(scores), self.feature_importance
