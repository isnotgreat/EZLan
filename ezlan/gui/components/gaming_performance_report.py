from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QLabel
import pyqtgraph as pg
import numpy as np

class GamingPerformanceReport(QDialog):
    def __init__(self, tunnel_service, user_name, parent=None):
        super().__init__(parent)
        self.tunnel_service = tunnel_service
        self.user_name = user_name
        self.setWindowTitle("Gaming Performance Analysis")
        self.setMinimumSize(900, 700)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        
        # Real-time performance tab
        performance_widget = self._create_performance_tab()
        tab_widget.addTab(performance_widget, "Real-time Performance")
        
        # Historical analysis tab
        history_widget = self._create_history_tab()
        tab_widget.addTab(history_widget, "Performance History")
        
        # Optimization suggestions tab
        optimization_widget = self._create_optimization_tab()
        tab_widget.addTab(optimization_widget, "Optimization Suggestions")
        
        layout.addWidget(tab_widget)
        
    def _create_performance_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Frame time plot
        frame_plot = pg.PlotWidget(title="Frame Time Distribution")
        frame_plot.setLabel('left', 'Count')
        frame_plot.setLabel('bottom', 'Frame Time (ms)')
        layout.addWidget(frame_plot)
        
        # Network stability plot
        stability_plot = pg.PlotWidget(title="Network Stability")
        stability_plot.setLabel('left', 'Stability Score')
        stability_plot.setLabel('bottom', 'Time (s)')
        layout.addWidget(stability_plot)
        
        return widget 