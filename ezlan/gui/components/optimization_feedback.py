from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import QTimer
from ezlan.network.tunnel import TunnelService

class OptimizationFeedbackWidget(QWidget):
    def __init__(self, tunnel_service: TunnelService, username: str):
        super().__init__()
        self.tunnel_service = tunnel_service
        self.username = username
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_feedback)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Connection Optimization Feedback")
        layout.addWidget(title_label)
        
        # Feedback text area
        self.feedback_text = QTextEdit()
        self.feedback_text.setReadOnly(True)
        self.feedback_text.setMaximumHeight(100)
        layout.addWidget(self.feedback_text)
        
    def set_user(self, username: str):
        """Update the username for feedback"""
        self.username = username
        self.update_feedback()
        
    def update_feedback(self):
        """Update the optimization feedback based on current metrics"""
        if not self.username:
            self.feedback_text.setText("No active connection")
            return
            
        try:
            metrics = self.tunnel_service.network_analytics.get_current_metrics(self.username)
            if not metrics:
                self.feedback_text.setText("No metrics available")
                return
                
            feedback = []
            
            # Analyze latency
            if metrics.avg_latency > 100:
                feedback.append("High latency detected. Consider optimizing network conditions.")
            
            # Analyze packet loss
            if metrics.packet_loss > 0.02:  # 2% packet loss
                feedback.append("Significant packet loss observed. Check network stability.")
            
            # Analyze bandwidth
            if metrics.bandwidth_utilization < 500000:  # 500KB/s
                feedback.append("Low bandwidth utilization. Connection might be throttled.")
            
            # Set feedback text
            if feedback:
                self.feedback_text.setText("\n".join(feedback))
            else:
                self.feedback_text.setText("Connection is performing optimally")
                
        except Exception as e:
            self.feedback_text.setText(f"Error getting metrics: {str(e)}")
