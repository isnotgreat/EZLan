from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QTimer

class GamingFeedbackWidget(QWidget):
    def __init__(self, tunnel_service, username: str):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.username = username
        self.setup_ui()
        
        # Update more frequently for gaming feedback
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_feedback)
        self.update_timer.start(1000)  # Update every second
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Gaming performance indicators
        self.latency_bar = self._create_performance_bar("Latency")
        self.stability_bar = self._create_performance_bar("Connection Stability")
        self.packet_timing_bar = self._create_performance_bar("Packet Timing")
        
        # Real-time feedback label
        self.feedback_label = QLabel("Monitoring gaming performance...")
        layout.addWidget(self.feedback_label) 