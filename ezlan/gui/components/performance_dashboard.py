from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTabWidget, QProgressBar, QPushButton)
from PyQt6.QtCore import QTimer
import pyqtgraph as pg
import numpy as np
import qasync
import asyncio

class PerformanceDashboard(QWidget):
    def __init__(self, tunnel_service, parent=None):
        super().__init__(parent)
        self.tunnel_service = tunnel_service
        self.setMinimumWidth(400)
        self.history_length = 60  # 60 seconds of history
        self.user_plots = {}  # Store plots for each user
        self._running = True
        self._setup_ui()
        
        # Start the update loop using qasync
        self.start_update_loop()
        
    def start_update_loop(self):
        """Start the async update loop"""
        loop = asyncio.get_event_loop()
        self.update_task = loop.create_task(self._update_loop())
        
    async def _update_loop(self):
        """Async loop to update metrics"""
        while self._running:
            try:
                await self.update_metrics()
                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                self.logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
                
    @qasync.asyncSlot()
    async def update_metrics(self):
        """Update metrics for all active connections"""
        try:
            for user_name, tunnel in self.tunnel_service.active_tunnels.items():
                metrics = self.tunnel_service.network_analytics.get_current_metrics(user_name)
                
                # Add user tab if it doesn't exist
                if not any(user_name in self.tab_widget.tabText(i) for i in range(self.tab_widget.count())):
                    self.add_user_tab(user_name)
                
                # Update plots only if we have metrics
                if metrics:
                    self.update_user_plots(user_name, metrics)
                    
                # Update health score (will be 0 if no metrics)
                health_score = self.calculate_health_score(metrics)
                self.health_score.setValue(int(health_score * 100))
                
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
            
    def closeEvent(self, event):
        """Handle widget close event"""
        self._running = False
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
        super().closeEvent(event)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)
        
        # Network health score
        self.health_score = QProgressBar()
        self.health_score.setRange(0, 100)
        overview_layout.addWidget(QLabel("Network Health Score"))
        overview_layout.addWidget(self.health_score)
        
        # Real-time graphs
        self.latency_plot = self.create_plot("Latency (ms)")
        self.bandwidth_plot = self.create_plot("Bandwidth (MB/s)")
        self.packet_loss_plot = self.create_plot("Packet Loss (%)")
        
        overview_layout.addWidget(self.latency_plot)
        overview_layout.addWidget(self.bandwidth_plot)
        overview_layout.addWidget(self.packet_loss_plot)
        
        self.tab_widget.addTab(overview_widget, "Overview")
        
    def create_plot(self, title):
        plot_widget = pg.PlotWidget()
        plot_widget.setTitle(title)
        plot_widget.setLabel('left', title)
        plot_widget.setLabel('bottom', 'Time (s)')
        plot_widget.showGrid(x=True, y=True)
        return plot_widget
        
    def add_user_tab(self, user_name):
        """Add a new tab for a user's metrics"""
        # Create a new widget for the user's metrics
        user_widget = QWidget()
        layout = QVBoxLayout(user_widget)
        
        # Create plots for this user
        latency_plot = self.create_plot("Latency (ms)")
        bandwidth_plot = self.create_plot("Bandwidth (MB/s)")
        packet_loss_plot = self.create_plot("Packet Loss (%)")
        
        layout.addWidget(latency_plot)
        layout.addWidget(bandwidth_plot)
        layout.addWidget(packet_loss_plot)
        
        # Store the plots for updates
        self.user_plots[user_name] = {
            'latency': latency_plot,
            'bandwidth': bandwidth_plot,
            'packet_loss': packet_loss_plot
        }
        
        # Add the tab
        self.tab_widget.addTab(user_widget, user_name)
        
    def update_user_plots(self, user_name, metrics):
        """Update the plots for a specific user"""
        if user_name not in self.user_plots:
            return
            
        plots = self.user_plots[user_name]
        
        # Update each plot with new data
        if metrics:
            plots['latency'].plot([metrics.avg_latency])
            plots['bandwidth'].plot([metrics.bandwidth_utilization / (1024*1024)])  # Convert to MB/s
            plots['packet_loss'].plot([metrics.packet_loss * 100])  # Convert to percentage
            
    def calculate_health_score(self, metrics):
        """Calculate overall health score based on multiple metrics"""
        if not metrics:
            return 0.0  # Return 0 if no metrics available
        
        try:
            # Calculate individual scores with safety checks
            latency_score = max(0, 1 - (metrics.avg_latency / 200)) if metrics.avg_latency is not None else 0
            packet_loss_score = max(0, 1 - (metrics.packet_loss * 20)) if metrics.packet_loss is not None else 0
            bandwidth_score = min(1, metrics.bandwidth_utilization / (1024 * 1024)) if metrics.bandwidth_utilization is not None else 0
            
            # Calculate weighted average
            return (latency_score * 0.4 + packet_loss_score * 0.4 + bandwidth_score * 0.2)
            
        except Exception as e:
            self.logger.error(f"Error calculating health score: {e}")
            return 0.0

    def _cleanup(self):
        """Clean up resources"""
        self._running = False
        # Add any additional cleanup needed
    
    def remove_user_tab(self, user_name):
        """Remove a user's tab and cleanup their plots"""
        for i in range(self.tab_widget.count()):
            if user_name in self.tab_widget.tabText(i):
                self.tab_widget.removeTab(i)
                if user_name in self.user_plots:
                    del self.user_plots[user_name]
                break
        
        # Reset health score when no connections are active
        if not self.user_plots:
            self.health_score.setValue(0)

