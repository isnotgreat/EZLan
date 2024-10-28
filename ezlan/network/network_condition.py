from dataclasses import dataclass

@dataclass
class NetworkCondition:
    latency: float
    bandwidth: float
    packet_loss: float
    jitter: float
    connection_stability: float
