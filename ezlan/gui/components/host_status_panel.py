from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                           QPushButton, QListWidget, QHBoxLayout)
from PyQt6.QtCore import Qt

class HostStatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.hide()  # Hidden by default
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Host info section
        self.host_info_label = QLabel("Not Hosting")
        layout.addWidget(self.host_info_label)
        
        # Connected clients list
        layout.addWidget(QLabel("Connected Clients:"))
        self.clients_list = QListWidget()
        layout.addWidget(self.clients_list)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        self.stop_btn = QPushButton("Stop Hosting")
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
    
    def update_host_info(self, host_info):
        self.host_info_label.setText(
            f"Hosting Network: {host_info['name']}\n"
            f"IP: {host_info['public_ip']}\n"
            f"Port: {host_info['port']}"
        )
        self.show()
    
    def add_client(self, client_info):
        self.clients_list.addItem(f"{client_info['name']} ({client_info['ip']})")
    
    def remove_client(self, client_name):
        items = self.clients_list.findItems(client_name, Qt.MatchStartsWith)
        for item in items:
            self.clients_list.takeItem(self.clients_list.row(item))
