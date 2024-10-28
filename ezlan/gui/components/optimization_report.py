from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, 
                           QTableWidget, QTableWidgetItem)
import pyqtgraph as pg

class OptimizationReportDialog(QDialog):
    def __init__(self, optimization_result, parent=None):
        super().__init__(parent)
        self.result = optimization_result
        self.setWindowTitle("Optimization Report")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        
        # Summary tab
        summary_widget = self._create_summary_tab()
        tab_widget.addTab(summary_widget, "Summary")
        
        # Metrics comparison tab
        comparison_widget = self._create_comparison_tab()
        tab_widget.addTab(comparison_widget, "Metrics Comparison")
        
        # AB Testing results tab
        ab_widget = self._create_ab_test_tab()
        tab_widget.addTab(ab_widget, "A/B Test Results")
        
        layout.addWidget(tab_widget)
        
    def _create_comparison_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create before/after graphs
        for metric in ['latency', 'bandwidth', 'packet_loss']:
            plot = pg.PlotWidget()
            plot.setTitle(f"{metric.title()} Comparison")
            plot.addLegend()
            
            # Plot before data
            before_curve = plot.plot(
                self.result.metrics_before[metric],
                pen='b',
                name='Before'
            )
            
            # Plot after data
            after_curve = plot.plot(
                self.result.metrics_after[metric],
                pen='g',
                name='After'
            )
            
            layout.addWidget(plot)
            
        return widget
