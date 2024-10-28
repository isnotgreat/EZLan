from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from ezlan.network.discovery import DiscoveryService

class UserList(QListWidget):
    user_selected = pyqtSignal(dict)
    
    def __init__(self, discovery_service: DiscoveryService):
        super().__init__()
        self.discovery_service = discovery_service
        
        # Connect signals
        self.discovery_service.users_updated.connect(self.update_users)
        self.discovery_service.peer_discovered.connect(self._handle_peer_discovered)
        self.discovery_service.peer_lost.connect(self._handle_peer_lost)
        
        # Initial population
        self.update_users(self.discovery_service.get_known_peers())
        
        # Handle double click
        self.itemDoubleClicked.connect(self.on_user_selected)
        
    def update_users(self, users):
        """Update the list with current users"""
        self.clear()
        for user in users:
            self.add_user(user)
            
    def add_user(self, user_info):
        """Add a single user to the list"""
        item = QListWidgetItem(f"{user_info['name']} ({user_info['ip']})")
        item.setData(1, user_info)  # Store full user info in item data
        self.addItem(item)
        
    def remove_user(self, username):
        """Remove a user from the list"""
        items = self.findItems(username, Qt.MatchStartsWith)
        for item in items:
            self.takeItem(self.row(item))
            
    def _handle_peer_discovered(self, peer_info):
        """Handle peer discovered signal"""
        self.add_user(peer_info)
        
    def _handle_peer_lost(self, peer_name):
        """Handle peer lost signal"""
        self.remove_user(peer_name)
        
    def on_user_selected(self, item):
        user_data = item.data(1)
        self.user_selected.emit(user_data)
