from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLineEdit, QLabel, QTabWidget, 
                           QListWidget, QWidget, QListWidgetItem, QMessageBox, QComboBox)
from ezlan.network.tunnel import TunnelService
from ezlan.utils.host_storage import HostStorage
from PyQt6.QtCore import Qt
import qasync

class ConnectionDialog(QDialog):
    def __init__(self, parent, tunnel_service):
        super().__init__(parent)
        self.tunnel_service = tunnel_service
        self.host_storage = HostStorage()
        self.connection_in_progress = False
        self.setup_ui()
        
    @qasync.asyncSlot()
    async def accept(self):
        if self.connection_in_progress:
            return
            
        self.connection_in_progress = True
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        
        try:
            conn_info = self.get_connection_info()
            if conn_info['type'] == 'direct':
                success = await self.tunnel_service.connect_to_host(
                    conn_info['ip'],
                    conn_info['port'],
                    conn_info['password']
                )
                if success:
                    super().accept()
                else:
                    QMessageBox.critical(
                        self,
                        "Connection Failed",
                        "Failed to establish connection. Please check the IP, port and password."
                    )
            else:
                # Handle local peer connection
                self.tunnel_service.connect_to_peer(conn_info['peer'])
                super().accept()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Connection failed: {str(e)}"
            )
        finally:
            self.connection_in_progress = False
            self.connect_btn.setEnabled(True)
            self.connect_btn.setText("Connect")
    
    def setup_ui(self):
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
        
        # Host selection combo box
        self.host_combo = QComboBox()
        self.host_combo.setEditable(True)
        self.host_combo.currentTextChanged.connect(self._on_host_selected)
        self._populate_hosts()
        
        # Input fields
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.port_input.setText("12345")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Remove host button
        remove_btn = QPushButton("Remove Host")
        remove_btn.clicked.connect(self._remove_current_host)
        
        # Add all widgets to layout
        remote_layout.addWidget(QLabel("Saved Hosts:"))
        remote_layout.addWidget(self.host_combo)
        remote_layout.addWidget(remove_btn)
        remote_layout.addWidget(QLabel("IP:"))
        remote_layout.addWidget(self.ip_input)
        remote_layout.addWidget(QLabel("Port:"))
        remote_layout.addWidget(self.port_input)
        remote_layout.addWidget(QLabel("Password:"))
        remote_layout.addWidget(self.password_input)
        
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
    
    def _populate_hosts(self):
        self.host_combo.clear()
        self.host_combo.addItem("")  # Empty option
        for host_key, host_info in self.host_storage.get_hosts().items():
            self.host_combo.addItem(host_key)

    def _on_host_selected(self, host_key):
        if host_key in self.host_storage.get_hosts():
            host = self.host_storage.get_hosts()[host_key]
            self.ip_input.setText(host['ip'])
            self.port_input.setText(str(host['port']))
            self.password_input.setText(host['password'])

    def _remove_current_host(self):
        host_key = self.host_combo.currentText()
        if host_key in self.host_storage.get_hosts():
            self.host_storage.remove_host(
                self.host_storage.get_hosts()[host_key]['ip'],
                self.host_storage.get_hosts()[host_key]['port']
            )
            self._populate_hosts()

    def get_connection_info(self):
        ip = self.ip_input.text().strip()
        try:
            port = int(self.port_input.text())
        except ValueError:
            port = 12345
            
        # Save host info
        self.host_storage.add_host(ip, port, self.password_input.text())
        
        return {
            'type': 'direct',
            'ip': ip,
            'port': port,
            'password': self.password_input.text()
        }
