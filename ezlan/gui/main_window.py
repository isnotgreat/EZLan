from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLineEdit, QLabel, QHBoxLayout,
                           QSplitter, QMessageBox)
from PyQt6.QtCore import Qt
from .components.user_list import UserList
from .components.connection_dialog import ConnectionDialog
from .components.connection_status import ConnectionStatusWidget
from .components.performance_dashboard import PerformanceDashboard
from .components.quality_widget import QualityWidget
from .components.optimization_feedback import OptimizationFeedbackWidget
from ezlan.network.monitor import ConnectionMonitor
from ezlan.network.discovery import DiscoveryService
from ezlan.network.tunnel import TunnelService
from ezlan.utils.logger import Logger
from .components.host_dialog import HostDialog  # Add this import
from .components.host_status_panel import HostStatusPanel

class MainWindow(QMainWindow):
    def __init__(self, discovery_service: DiscoveryService, tunnel_service: TunnelService):
        super().__init__()
        self.logger = Logger("MainWindow")
        self.discovery_service = discovery_service
        self.tunnel_service = tunnel_service
        self.connection_monitor = ConnectionMonitor(tunnel_service)
        
        self.setWindowTitle("EZLan")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add widgets
        self._setup_ui(layout)
        
        # Setup connections with error handling
        try:
            self._setup_connections()
        except Exception as e:
            self.logger.warning(f"Failed to setup some connections: {e}")
            # Continue without discovery service connections
            self._setup_basic_connections()
            
        self.logger.info("MainWindow initialized")
    
    def _setup_basic_connections(self):
        """Setup only essential connections that don't depend on discovery"""
        self.host_status.stop_btn.clicked.connect(self._stop_hosting)
        self.host_btn.clicked.connect(self._show_host_dialog)
        self.connect_btn.clicked.connect(self._show_connection_dialog)
        self.disconnect_btn.clicked.connect(self._handle_disconnect)
        self.tunnel_service.connection_established.connect(self._handle_connection_established)
        self.tunnel_service.connection_failed.connect(self._handle_connection_failed)
        self.tunnel_service.connection_closed.connect(self._handle_connection_closed)
        self.tunnel_service.host_started.connect(self._handle_host_started)
    
    def _setup_ui(self, layout):
        # Add host status panel at the top
        self.host_status = HostStatusPanel()
        layout.addWidget(self.host_status)
        
        # Create top control panel
        control_panel = QHBoxLayout()
        
        # Host button
        self.host_btn = QPushButton("Host Network")
        control_panel.addWidget(self.host_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect to Network")
        control_panel.addWidget(self.connect_btn)
        
        # Disconnect button
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)  # Disabled by default
        control_panel.addWidget(self.disconnect_btn)
        
        # Add control panel to main layout
        layout.addLayout(control_panel)
        
        # Create main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - User list and connection status
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.user_list = UserList(self.discovery_service)
        left_layout.addWidget(self.user_list)
        # Pass the connection_monitor as monitor_service
        self.connection_status = ConnectionStatusWidget(monitor_service=self.connection_monitor)
        left_layout.addWidget(self.connection_status)
        
        # Right panel - Performance metrics and quality
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.performance_dashboard = PerformanceDashboard(self.tunnel_service)
        self.quality_widget = QualityWidget()
        self.optimization_feedback = OptimizationFeedbackWidget(self.tunnel_service, "")
        right_layout.addWidget(self.performance_dashboard)
        right_layout.addWidget(self.quality_widget)
        right_layout.addWidget(self.optimization_feedback)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Add splitter to main layout
        layout.addWidget(splitter)
    
    def _setup_connections(self):
        # Add host status panel connections
        self.host_status.stop_btn.clicked.connect(self._stop_hosting)
        
        # Add host button connection
        self.host_btn.clicked.connect(self._show_host_dialog)
        
        # Update existing connections
        self.connect_btn.clicked.connect(self._show_connection_dialog)
        self.disconnect_btn.clicked.connect(self._handle_disconnect)
        self.discovery_service.peer_discovered.connect(self.user_list.add_user)
        self.discovery_service.peer_lost.connect(self.user_list.remove_user)
        self.tunnel_service.connection_established.connect(self._handle_connection_established)
        self.tunnel_service.connection_failed.connect(self._handle_connection_failed)
        self.tunnel_service.connection_closed.connect(self._handle_connection_closed)
        self.tunnel_service.host_started.connect(self._handle_host_started)
    
    def _show_host_dialog(self):
        dialog = HostDialog(self)
        if dialog.exec():
            host_info = dialog.get_host_info()
            self.tunnel_service.start_hosting(
                host_info['name'],
                host_info['password'],
                host_info.get('port', 12345)
            )

    def _show_connection_dialog(self):
        dialog = ConnectionDialog(self, self.tunnel_service)
        if dialog.exec():
            conn_info = dialog.get_connection_info()
            if conn_info:  # Add null check
                if conn_info['type'] == 'local':
                    self.tunnel_service.connect_to_peer(conn_info['peer'])
                else:
                    self.tunnel_service.connect_to_host(
                        conn_info['ip'],
                        conn_info['port'],
                        conn_info['password']
                    )

    def _handle_connection_established(self, peer_info):
        self.connection_monitor.start_monitoring(peer_info['name'], peer_info['ip'])
        self.optimization_feedback.set_user(peer_info['name'])
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.logger.info(f"Connection established with {peer_info['name']}")
    
    def _handle_connection_failed(self, error):
        self.logger.error(f"Connection failed: {error}")

    def _handle_host_started(self, host_info):
        self.host_status.update_host_info(host_info)
        self.host_btn.setEnabled(False)  # Disable host button while hosting
        QMessageBox.information(
            self,
            "Hosting Started",
            f"Network is now hosted at:\nIP: {host_info['public_ip']}\nPort: {host_info['port']}"
        )

    def _stop_hosting(self):
        self.tunnel_service.stop_hosting()
        self.host_status.hide()
        self.host_btn.setEnabled(True)

    def _handle_connection_closed(self, peer_name):
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.optimization_feedback.set_user("")
        self.logger.info(f"Connection closed with {peer_name}")

    def _handle_disconnect(self):
        """Handle disconnect button click"""
        try:
            # Get the current connected peer name from active tunnels
            active_peers = list(self.tunnel_service.active_tunnels.keys())
            if active_peers:
                peer_name = active_peers[0]  # Get the first (and should be only) active peer
                
                # Disconnect from peer
                self.tunnel_service.disconnect_from_peer(peer_name)
                
                # Update UI
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                
                # Clean up performance dashboard
                for i in range(self.performance_dashboard.tab_widget.count()):
                    if peer_name in self.performance_dashboard.tab_widget.tabText(i):
                        self.performance_dashboard.tab_widget.removeTab(i)
                        if peer_name in self.performance_dashboard.user_plots:
                            del self.performance_dashboard.user_plots[peer_name]
                        break
                
                # Reset other UI elements
                self.optimization_feedback.set_user("")
                self.quality_widget.update_quality(1.0)  # Reset quality to default
                self.connection_status.update_status("Disconnected")
                
                self.logger.info(f"Disconnected from {peer_name}")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
            QMessageBox.critical(self, "Error", f"Failed to disconnect: {str(e)}")
