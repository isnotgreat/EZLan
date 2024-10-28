from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLineEdit, QLabel, QTabWidget, 
                           QListWidget, QWidget, QListWidgetItem)
from ezlan.network.tunnel import TunnelService
from PyQt6.QtCore import Qt

class ConnectionDialog(QDialog):
    def __init__(self, parent, tunnel_service: TunnelService):
        super().__init__(parent)
        self.tunnel_service = tunnel_service
        self.setWindowTitle("Connect to Network")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()  # Make it instance variable
        layout.addWidget(self.tabs)
        
        # Local peers tab
        local_tab = QWidget()
        local_layout = QVBoxLayout(local_tab)
        self.peer_list = QListWidget()
        local_layout.addWidget(QLabel("Available Local Peers:"))
        local_layout.addWidget(self.peer_list)
        self.tabs.addTab(local_tab, "Local Peers")
        
        # Remote host tab
        remote_tab = QWidget()
        remote_layout = QVBoxLayout(remote_tab)
        
        remote_layout.addWidget(QLabel("Host IP:"))
        self.ip_edit = QLineEdit()
        remote_layout.addWidget(self.ip_edit)
        
        remote_layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit("12345")
        remote_layout.addWidget(self.port_edit)
        
        remote_layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        remote_layout.addWidget(self.password_edit)
        
        self.tabs.addTab(remote_tab, "Remote Host")
        
        # Buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.connect_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Populate local peers
        self.populate_peers()
    
    def populate_peers(self):
        """Populate the list of discovered peers"""
        discovered_peers = self.parent().discovery_service.get_discovered_peers()
        for peer in discovered_peers:
            item = QListWidgetItem(f"{peer['name']} ({peer['ip']})")
            item.setData(Qt.ItemDataRole.UserRole, peer)
            self.peer_list.addItem(item)
    
    def get_connection_info(self):
        """Get the connection information based on selected tab"""
        if self.tabs.currentIndex() == 0:  # Local peers
            selected_items = self.peer_list.selectedItems()
            if not selected_items:
                return None
            return {
                'type': 'local',
                'peer': selected_items[0].data(Qt.ItemDataRole.UserRole)
            }
        else:  # Remote host
            return {
                'type': 'remote',
                'ip': self.ip_edit.text(),
                'port': int(self.port_edit.text()),
                'password': self.password_edit.text()
            }
