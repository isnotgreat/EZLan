from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QTabWidget
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import numpy as np

class GamingPerformanceWidget(QWidget):
    def __init__(self, tunnel_service, username: str):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.username = username
        self.history_size = 120  # 2 minutes of history
        self.setup_ui()
        
        # Update more frequently for gaming metrics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Update every second
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        
        # Real-time metrics tab
        metrics_widget = self._create_metrics_tab()
        tab_widget.addTab(metrics_widget, "Real-time Metrics")
        
        # Performance graphs tab
        graphs_widget = self._create_graphs_tab()
        tab_widget.addTab(graphs_widget, "Performance Graphs")
        
        layout.addWidget(tab_widget)
        
    def _create_metrics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Frame time indicator
        self.frame_time_label = QLabel("Frame Time: -- ms")
        self.frame_time_bar = QProgressBar()
        self.frame_time_bar.setRange(0, 100)
        layout.addWidget(self.frame_time_label)
        layout.addWidget(self.frame_time_bar)
        
        # Network stability indicator
        self.stability_label = QLabel("Network Stability: --%")
        self.stability_bar = QProgressBar()
        self.stability_bar.setRange(0, 100)
        layout.addWidget(self.stability_label)
        layout.addWidget(self.stability_bar)
        
        return widget 