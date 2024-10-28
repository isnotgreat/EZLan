from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class QualityWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection Quality Indicator
        self.quality_label = QLabel("Connection Quality")
        self.quality_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.quality_label)
        
        # Quality Progress Bar
        self.quality_bar = QProgressBar()
        self.quality_bar.setRange(0, 100)
        self.quality_bar.setValue(100)  # Default value
        layout.addWidget(self.quality_bar)
        
        # Status Label
        self.status_label = QLabel("Excellent")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def update_quality(self, quality_score: float):
        """
        Update the quality widget with a new score
        
        Args:
            quality_score (float): Score between 0 and 1
        """
        score = int(quality_score * 100)
        self.quality_bar.setValue(score)
        
        # Update status text based on score
        if score >= 80:
            status = "Excellent"
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif score >= 60:
            status = "Good"
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: #8BC34A; }")
        elif score >= 40:
            status = "Fair"
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")
        elif score >= 20:
            status = "Poor"
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF9800; }")
        else:
            status = "Critical"
            self.quality_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
        
        self.status_label.setText(status)
