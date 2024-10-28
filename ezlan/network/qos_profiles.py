from dataclasses import dataclass
from typing import Dict

@dataclass
class QoSPreset:
    name: str
    priority: int
    bandwidth_limit: int  # KB/s
    latency_target: int  # ms
    description: str

class QoSProfileManager:
    def __init__(self):
        self.presets: Dict[str, QoSPreset] = {
            'gaming': QoSPreset(
                name='Gaming',
                priority=9,
                bandwidth_limit=1024,  # 1MB/s
                latency_target=20,
                description='Optimized for online gaming with low latency'
            ),
            'streaming': QoSPreset(
                name='Media Streaming',
                priority=7,
                bandwidth_limit=2048,  # 2MB/s
                latency_target=100,
                description='Balanced for media streaming applications'
            ),
            'file_transfer': QoSPreset(
                name='File Transfer',
                priority=5,
                bandwidth_limit=5120,  # 5MB/s
                latency_target=500,
                description='Maximum bandwidth for file transfers'
            ),
            'browsing': QoSPreset(
                name='Web Browsing',
                priority=3,
                bandwidth_limit=512,  # 512KB/s
                latency_target=200,
                description='Basic connectivity for web browsing'
            )
        }
