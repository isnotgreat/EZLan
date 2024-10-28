from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from ezlan.network.monitor import ConnectionMonitor

class ConnectionStatusWidget(QWidget):
    def __init__(self, monitor_service: ConnectionMonitor):
        super().__init__()
        self.monitor_service = monitor_service
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status Label
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Latency Display
        latency_container = QWidget()
        latency_layout = QVBoxLayout(latency_container)
        
        self.latency_label = QLabel("Latency: --")
        self.latency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        latency_layout.addWidget(self.latency_label)
        
        self.latency_bar = QProgressBar()
        self.latency_bar.setRange(0, 200)  # 0-200ms range
        self.latency_bar.setValue(0)
        latency_layout.addWidget(self.latency_bar)
        
        layout.addWidget(latency_container)
        
    def update_status(self, status: str):
        """Update the connection status display"""
        self.status_label.setText(f"Status: {status}")
        
        # Update color based on status
        if status == "Connected":
            self.status_label.setStyleSheet("color: green;")
        elif status == "Connecting":
            self.status_label.setStyleSheet("color: orange;")
        else:
            self.status_label.setStyleSheet("color: red;")
            
    def update_latency(self, latency: float):
        """Update the latency display"""
        if latency is None:
            self.latency_label.setText("Latency: --")
            self.latency_bar.setValue(0)
            return
            
        # Update latency label
        self.latency_label.setText(f"Latency: {latency:.1f}ms")
        
        # Update progress bar
        self.latency_bar.setValue(min(int(latency), 200))
        
        # Update color based on latency
        if latency < 50:
            self.latency_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #4CAF50; }
            """)
        elif latency < 100:
            self.latency_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #FFC107; }
            """)
        else:
            self.latency_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #F44336; }
            """)
