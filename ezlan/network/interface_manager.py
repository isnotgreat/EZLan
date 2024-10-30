from PyQt6.QtCore import QObject, pyqtSignal
from .hyperv_interface import HyperVInterfaceManager
from ..utils.logger import Logger
import time
import subprocess
import asyncio

class InterfaceManager(QObject):
    interface_created = pyqtSignal(str)  # interface_name
    interface_error = pyqtSignal(str)    # error_message

    def __init__(self):
        super().__init__()
        self.logger = Logger("InterfaceManager")
        self.interface_manager = HyperVInterfaceManager()
        self.is_active = False

        # Connect signals from HyperVInterfaceManager to InterfaceManager's handlers
        self.interface_manager.interface_created.connect(self.on_interface_created)
        self.interface_manager.interface_error.connect(self.on_interface_error)

    async def create_interface(self) -> bool:
        try:
            if self.is_active:
                self.logger.info("Interface already active.")
                return True

            success = await self.interface_manager.create_interface()
            if success:
                self.logger.info("Virtual interface creation succeeded.")
                await asyncio.sleep(2)  # Ensure interface is up
                self.is_active = True
                return True
            else:
                self.logger.error("Virtual interface creation failed.")
                return False

        except Exception as e:
            self.logger.error(f"Interface creation error: {str(e)}")
            return False

    def on_interface_created(self, interface_name):
        self.logger.info(f"Interface '{interface_name}' created successfully.")
        self.is_active = True
        self.interface_created.emit(interface_name)  # Emit InterfaceManager's signal

    def on_interface_error(self, error_message):
        self.logger.error(f"Interface creation error: {error_message}")
        self.is_active = False
        self.interface_error.emit(error_message)    # Emit InterfaceManager's signal

    async def cleanup_interface(self) -> bool:
        try:
            success = await self.interface_manager.cleanup_interface()
            if success:
                self.is_active = False
            return success
        except Exception as e:
            self.logger.error(f"Failed to cleanup interface: {e}")
            return False
