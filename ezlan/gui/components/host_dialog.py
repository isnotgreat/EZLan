from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, 
                           QPushButton, QLabel, QHBoxLayout)

class HostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Host Network")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Network name
        layout.addWidget(QLabel("Network Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)
        
        # Port
        layout.addWidget(QLabel("Port (optional):"))
        self.port_edit = QLineEdit()
        self.port_edit.setText("12345")
        layout.addWidget(self.port_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.host_btn = QPushButton("Start Hosting")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.host_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Connect buttons
        self.host_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    
    def get_host_info(self):
        return {
            'name': self.name_edit.text(),
            'password': self.password_edit.text(),
            'port': int(self.port_edit.text())
        }
