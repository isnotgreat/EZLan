from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                           QProgressBar, QTabWidget)
from PyQt6.QtCore import Qt

class DiagnosticsWidget(QWidget):
    def __init__(self, bandwidth_monitor, parent=None):
        super().__init__(parent)
        self.bandwidth_monitor = bandwidth_monitor
        self.connections = {}
        self.setup_ui()
        
        # Connect signals
        self.bandwidth_monitor.bandwidth_updated.connect(self.update_bandwidth)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add overview tab
        self.overview_tab = QWidget()
        self.overview_layout = QVBoxLayout(self.overview_tab)
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Add statistics label
        self.stats_label = QLabel("Network Statistics")
        self.stats_label.setStyleSheet("font-weight: bold;")
        self.overview_layout.addWidget(self.stats_label)
    
    def add_connection(self, user_name):
        if user_name not in self.connections:
            # Create connection tab
            connection_tab = QWidget()
            tab_layout = QVBoxLayout(connection_tab)
            
            # Upload speed
            upload_label = QLabel("Upload Speed (KB/s)")
            upload_bar = QProgressBar()
            upload_bar.setRange(0, 1000)
            
            # Download speed
            download_label = QLabel("Download Speed (KB/s)")
            download_bar = QProgressBar()
            download_bar.setRange(0, 1000)
            
            tab_layout.addWidget(upload_label)
            tab_layout.addWidget(upload_bar)
            tab_layout.addWidget(download_label)
            tab_layout.addWidget(download_bar)
            
            self.connections[user_name] = {
                'tab': connection_tab,
                'upload_bar': upload_bar,
                'download_bar': download_bar
            }
            
            self.tab_widget.addTab(connection_tab, user_name)
    
    def update_bandwidth(self, user_name, upload_speed, download_speed):
        if user_name in self.connections:
            self.connections[user_name]['upload_bar'].setValue(int(upload_speed))
            self.connections[user_name]['download_bar'].setValue(int(download_speed))
