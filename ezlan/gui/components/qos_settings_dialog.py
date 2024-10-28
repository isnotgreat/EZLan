from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QComboBox, QPushButton, QGroupBox, QMessageBox)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
from .optimization_report import OptimizationReportDialog
from .optimization_feedback import OptimizationFeedbackWidget
from .network_condition import NetworkCondition
from .advanced_visualization import AdvancedVisualizationWidget

class QoSSettingsDialog(QDialog):
    def __init__(self, tunnel_service, user_name, parent=None):
        super().__init__(parent)
        self.tunnel_service = tunnel_service
        self.user_name = user_name
        self.setWindowTitle(f"QoS Settings - {user_name}")
        self.setMinimumSize(600, 400)
        
        self.bandwidth_data = []
        self.latency_data = []
        self.setup_ui()
        
        # Start monitoring timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_graphs)
        self.update_timer.start(1000)  # Update every second
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Preset selection
        preset_group = QGroupBox("QoS Preset")
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.tunnel_service.qos_profiles.presets.keys())
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        preset_layout.addWidget(self.preset_combo)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Custom settings
        settings_group = QGroupBox("Custom Settings")
        settings_layout = QVBoxLayout()
        
        # Priority settings
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority:"))
        self.priority_box = QSpinBox()
        self.priority_box.setRange(0, 9)
        self.priority_box.setValue(5)
        priority_layout.addWidget(self.priority_box)
        settings_layout.addLayout(priority_layout)
        
        # Bandwidth limit
        bandwidth_layout = QHBoxLayout()
        bandwidth_layout.addWidget(QLabel("Bandwidth Limit:"))
        self.bandwidth_box = QSpinBox()
        self.bandwidth_box.setRange(0, 1000)
        self.bandwidth_box.setValue(100)
        bandwidth_layout.addWidget(self.bandwidth_box)
        self.bandwidth_unit = QComboBox()
        self.bandwidth_unit.addItems(["KB/s", "MB/s"])
        bandwidth_layout.addWidget(self.bandwidth_unit)
        settings_layout.addLayout(bandwidth_layout)
        
        # Latency target
        latency_layout = QHBoxLayout()
        latency_layout.addWidget(QLabel("Latency Target (ms):"))
        self.latency_box = QSpinBox()
        self.latency_box.setRange(0, 1000)
        self.latency_box.setValue(50)
        latency_layout.addWidget(self.latency_box)
        settings_layout.addLayout(latency_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Monitoring graphs
        graphs_group = QGroupBox("Real-time Monitoring")
        graphs_layout = QHBoxLayout()
        
        # Bandwidth graph
        self.bandwidth_plot = pg.PlotWidget()
        self.bandwidth_plot.setTitle("Bandwidth Usage")
        self.bandwidth_plot.setLabel('left', 'KB/s')
        self.bandwidth_curve = self.bandwidth_plot.plot(pen='g')
        
        # Latency graph
        self.latency_plot = pg.PlotWidget()
        self.latency_plot.setTitle("Latency")
        self.latency_plot.setLabel('left', 'ms')
        self.latency_curve = self.latency_plot.plot(pen='b')
        
        graphs_layout.addWidget(self.bandwidth_plot)
        graphs_layout.addWidget(self.latency_plot)
        graphs_group.setLayout(graphs_layout)
        layout.addWidget(graphs_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Add to setup_ui method
        optimization_group = QGroupBox("Automatic Optimization")
        optimization_layout = QVBoxLayout()

        self.auto_optimize_button = QPushButton("Start Auto-Optimization")
        self.auto_optimize_button.clicked.connect(self.toggle_auto_optimization)
        optimization_layout.addWidget(self.auto_optimize_button)

        self.optimization_status = QLabel("Status: Not running")
        optimization_layout.addWidget(self.optimization_status)

        # Strategy selection
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Optimization Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([s.value for s in OptimizationStrategy])
        strategy_layout.addWidget(self.strategy_combo)
        optimization_layout.addLayout(strategy_layout)
        
        # View report button
        self.report_button = QPushButton("View Optimization Report")
        self.report_button.clicked.connect(self.show_optimization_report)
        self.report_button.setEnabled(False)
        optimization_layout.addWidget(self.report_button)

        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        # Add optimization feedback widget
        self.feedback_widget = OptimizationFeedbackWidget(
            self.tunnel_service, 
            self.user_name, 
            self
        )
        layout.addWidget(self.feedback_widget)
        
        # ML Strategy recommendation
        self.ml_recommendation = QLabel("AI Recommended Strategy: Analyzing...")
        optimization_layout.addWidget(self.ml_recommendation)
        
        # Update strategy periodically
        self.strategy_timer = QTimer()
        self.strategy_timer.timeout.connect(self.update_strategy_recommendation)
        self.strategy_timer.start(5000)  # Update every 5 seconds
        
        # Add advanced visualization
        self.visualization_widget = AdvancedVisualizationWidget(self)
        layout.addWidget(self.visualization_widget)
    
    def update_graphs(self):
        # Get current monitoring data
        bandwidth = self.tunnel_service.bandwidth_monitor.get_current_bandwidth(self.user_name)
        latency = self.tunnel_service.quality_monitor.get_current_latency(self.user_name)
        
        # Update data arrays
        self.bandwidth_data.append(bandwidth)
        self.latency_data.append(latency)
        
        # Keep last 60 seconds of data
        if len(self.bandwidth_data) > 60:
            self.bandwidth_data.pop(0)
        if len(self.latency_data) > 60:
            self.latency_data.pop(0)
        
        # Update graphs
        self.bandwidth_curve.setData(self.bandwidth_data)
        self.latency_curve.setData(self.latency_data)

    def toggle_auto_optimization(self):
        if self.auto_optimize_button.text() == "Start Auto-Optimization":
            self.tunnel_service.auto_optimizer.start_optimization(self.user_name)
            self.auto_optimize_button.setText("Stop Auto-Optimization")
            self.optimization_status.setText("Status: Running...")
        else:
            self.tunnel_service.auto_optimizer.stop_optimization(self.user_name)
            self.auto_optimize_button.setText("Start Auto-Optimization")
            self.optimization_status.setText("Status: Stopped")

    def show_optimization_report(self):
        if hasattr(self, 'last_optimization_result'):
            dialog = OptimizationReportDialog(self.last_optimization_result, self)
            dialog.exec()

    def update_strategy_recommendation(self):
        conditions = NetworkCondition(
            latency=np.mean(self.latency_data),
            bandwidth=np.mean(self.bandwidth_data),
            packet_loss=self.tunnel_service.quality_monitor.get_packet_loss(self.user_name),
            jitter=self.tunnel_service.quality_monitor.get_jitter(self.user_name),
            connection_stability=self.tunnel_service.network_analytics.get_stability(self.user_name)
        )
        
        recommended_strategy = self.tunnel_service.ml_strategy_selector.suggest_strategy(conditions)
        self.ml_recommendation.setText(f"AI Recommended Strategy: {recommended_strategy}")

    def load_preset(self, preset_name):
        if preset_name in self.tunnel_service.qos_profiles.presets:
            preset = self.tunnel_service.qos_profiles.presets[preset_name]
            self.priority_box.setValue(preset.priority)
            self.bandwidth_box.setValue(preset.bandwidth_limit // 1024)  # Convert to KB/s
            self.latency_box.setValue(preset.latency_target)

    def apply_settings(self):
        try:
            bandwidth = self.bandwidth_box.value()
            if self.bandwidth_unit.currentText() == "MB/s":
                bandwidth *= 1024  # Convert to KB/s
            
            policy = QoSPolicy(
                priority=self.priority_box.value(),
                bandwidth_limit=bandwidth * 1024,  # Convert to bytes/s
                latency_target=self.latency_box.value()
            )
            
            self.tunnel_service.traffic_shaper.update_policy(self.user_name, policy)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
