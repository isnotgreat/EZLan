from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLineEdit, QLabel, QHBoxLayout,
                           QSplitter, QMessageBox, QApplication, QToolTip)
from PyQt6.QtCore import Qt, pyqtSlot, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QMouseEvent
import qasync
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
import asyncio

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                color: blue;
                text-decoration: underline;
                padding: 5px;
            }
            QLabel:hover {
                color: darkblue;
            }
        """)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

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
        """Setup signal connections"""
        try:
            # Add host status panel connections
            self.host_status.stop_btn.clicked.connect(self._stop_hosting)
            
            # Add host button connection
            self.host_btn.clicked.connect(self._show_host_dialog)
            
            # Add connect button connection
            self.connect_btn.clicked.connect(self._show_connection_dialog)
            
            # Add disconnect button connection
            self.disconnect_btn.clicked.connect(self._handle_disconnect)
            
            # Add discovery service connections
            self.discovery_service.peer_discovered.connect(self.user_list.add_user)
            self.discovery_service.peer_lost.connect(self.user_list.remove_user)
            
            # Add tunnel service connections
            self.tunnel_service.connection_established.connect(self._handle_connection_established)
            self.tunnel_service.connection_failed.connect(self._handle_connection_failed)
            self.tunnel_service.connection_closed.connect(self._handle_connection_closed)
            self.tunnel_service.host_started.connect(self._handle_host_started)
            
        except Exception as e:
            self.logger.warning(f"Failed to setup some connections: {e}")
            # Fall back to basic connections
            self._setup_basic_connections()
    
    @pyqtSlot(dict)
    def _handle_host_started(self, host_info):
        """Handle when hosting starts"""
        public_ip = host_info.get('public_ip', 'Unknown')
        tunnel_port = host_info.get('port', '12345')
        self.host_status.update_host_info(host_info)
        self.host_btn.setEnabled(False)
        self.host_status.stop_btn.setEnabled(True)
        
        # Create clickable message box with IP and port
        msg = QMessageBox(self)
        msg.setWindowTitle("Hosting Started")
        msg.setText("Network is now hosted at:")
        
        # Create layout for IP and port
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add clickable IP label
        ip_label = ClickableLabel(f"IP: {public_ip}")
        ip_label.clicked.connect(lambda: self._copy_to_clipboard(public_ip))
        layout.addWidget(ip_label)
        
        # Add clickable port label
        port_label = ClickableLabel(f"Port: {tunnel_port}")
        port_label.clicked.connect(lambda: self._copy_to_clipboard(str(tunnel_port)))
        layout.addWidget(port_label)
        
        msg.layout().addWidget(widget, 1, 1)  # Add to message box layout
        msg.exec()

    @pyqtSlot(str)
    def _handle_host_failed(self, error_message):
        QMessageBox.critical(
            self,
            "Hosting Failed",
            f"Failed to start hosting: {error_message}"
        )
        self.host_btn.setEnabled(True)

    @pyqtSlot(str)
    def _handle_interface_created(self, interface_name):
        self.logger.info(f"Interface '{interface_name}' created successfully.")
        QMessageBox.information(
            self,
            "Interface Created",
            f"Virtual interface '{interface_name}' created successfully."
        )

    @pyqtSlot(str)
    def _handle_interface_error(self, error_message):
        self.logger.error(f"Interface creation failed: {error_message}")
        QMessageBox.critical(
            self,
            "Interface Creation Failed",
            f"Failed to create virtual interface: {error_message}"
        )
        self.host_btn.setEnabled(True)

    @qasync.asyncSlot()
    async def _stop_hosting(self):
        """Stop hosting and cleanup"""
        try:
            # Disable the stop button while processing
            self.host_status.stop_btn.setEnabled(False)
            await self.tunnel_service.stop_hosting()
            self.host_status.hide()
            self.host_btn.setEnabled(True)
            
            # Use QTimer to defer the message box
            QTimer.singleShot(0, lambda: QMessageBox.information(
                self,
                "Hosting Stopped",
                "The network hosting has been stopped."
            ))
        except Exception as e:
            self.logger.error(f"Failed to stop hosting: {e}")
            QTimer.singleShot(0, lambda: QMessageBox.critical(
                self,
                "Hosting Error",
                f"Failed to stop hosting: {str(e)}"
            ))
        finally:
            self.host_status.stop_btn.setEnabled(True)

    def _handle_connection_closed(self, peer_name):
        self.logger.info(f"Connection closed with {peer_name}")
        self.connection_monitor.stop_monitoring()
        self.optimization_feedback.clear_user()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        QMessageBox.information(
            self,
            "Connection Closed",
            f"Connection with {peer_name} has been closed."
        )

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

    def _handle_host_click(self):
        asyncio.create_task(self._start_hosting())

    def _show_connection_dialog(self):
        """Show dialog for connecting to a peer"""
        try:
            dialog = ConnectionDialog(self, self.tunnel_service)  # Pass tunnel_service here
            if dialog.exec():
                connection_info = dialog.get_connection_info()
                self.tunnel_service.connect_to_peer(
                    connection_info['host'],
                    connection_info['port'],
                    connection_info.get('password', '')
                )
        except Exception as e:
            self.logger.error(f"Failed to show connection dialog: {e}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect: {str(e)}"
            )

    def _show_host_dialog(self):
        """Show dialog for hosting"""
        try:
            dialog = HostDialog(self)
            if dialog.exec():
                host_info = dialog.get_host_info()
                # Use qasync's asyncSlot directly instead of creating a new task
                self._handle_host_start(host_info)
        except Exception as e:
            self.logger.error(f"Failed to show host dialog: {e}")
            QMessageBox.critical(
                self,
                "Hosting Error",
                f"Failed to show host dialog: {str(e)}"
            )

    @qasync.asyncSlot()
    async def _handle_host_start(self, host_info):
        """Handle the start hosting request"""
        try:
            await self.tunnel_service.start_hosting(host_info)
        except Exception as e:
            self.logger.error(f"Failed to start hosting: {e}")
            QMessageBox.critical(
                self,
                "Hosting Error",
                f"Failed to start hosting: {str(e)}"
            )

    @pyqtSlot(dict)
    def _handle_connection_established(self, peer_info):
        """Handle successful connection to peer"""
        self.logger.info(f"Connection established with {peer_info['name']}")
        self.connection_monitor.start_monitoring(peer_info['name'], peer_info['host'])
        self.optimization_feedback.set_user(peer_info['name'])
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.connection_status.update_status("Connected")
        QMessageBox.information(
            self,
            "Connection Established",
            f"Successfully connected to {peer_info['name']}"
        )

    @pyqtSlot(str)
    def _handle_connection_failed(self, error_message):
        """Handle failed connection attempt"""
        self.logger.error(f"Connection failed: {error_message}")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.connection_status.update_status("Disconnected")
        QMessageBox.critical(
            self,
            "Connection Failed",
            f"Failed to connect: {error_message}"
        )

    async def on_close_event(self):
        """Handle window close event and cleanup"""
        try:
            self.logger.info("Main window is closing.")
            
            # Stop all active connections first
            for peer_name in list(self.tunnel_service.active_tunnels.keys()):
                self.tunnel_service.disconnect_from_peer(peer_name)
            
            # Stop discovery service
            self.discovery_service.stop_discovery()
            
            # Stop hosting if active
            await self.tunnel_service.stop_hosting()
            
            # Close the window after cleanup
            QTimer.singleShot(0, self.close)
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def _copy_to_clipboard(self, text):
        """Copy text to clipboard and show feedback"""
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), "Copied to clipboard!", self)
