import sys
import ctypes
import traceback
import asyncio
import qasync
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from ezlan.gui.main_window import MainWindow
from ezlan.network.discovery import DiscoveryService
from ezlan.network.interface_manager import InterfaceManager
from ezlan.network.tunnel import TunnelService
from ezlan.utils.installer import SystemInstaller
from ezlan.utils.logger import Logger

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    """Restart the program with admin rights"""
    try:
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1
        )
        if ret <= 32:  # Error codes from ShellExecuteW
            raise RuntimeError(f"Failed to elevate privileges (error code: {ret})")
        return True
    except Exception as e:
        print(f"Failed to get admin rights: {e}")
        return False

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)
        self.logger = Logger("Application")
        self.installer = SystemInstaller()
        self.interface_manager = InterfaceManager()
        self.discovery_service = DiscoveryService()
        self.tunnel_service = TunnelService()
        self.main_window = MainWindow(self.discovery_service, self.tunnel_service)
        
        # Connect cleanup handlers
        self.app.aboutToQuit.connect(lambda: asyncio.create_task(self.cleanup()))

    async def cleanup(self):
        """Clean up resources before quitting"""
        try:
            # Stop all services in order
            if hasattr(self.discovery_service, '_running'):
                self.discovery_service.stop_discovery()
            
            # Stop all monitoring threads
            if hasattr(self.main_window, 'connection_monitor'):
                if hasattr(self.main_window.connection_monitor, 'stop'):
                    self.main_window.connection_monitor.stop()
            
            # Cleanup interface last
            if hasattr(self, 'interface_manager'):
                try:
                    await self.interface_manager.cleanup_interface()
                except Exception as e:
                    self.logger.error(f"Interface cleanup error: {e}")
                    
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
        finally:
            try:
                if asyncio.get_running_loop():
                    await asyncio.sleep(0.5)
            except RuntimeError:
                pass

    async def run(self):
        try:
            # Setup and show main window
            self.installer.check_and_setup()
            self.main_window.show()

            # Create virtual interface
            if not await self.interface_manager.create_interface():
                raise RuntimeError("Failed to create virtual interface")

            # Start discovery service
            self.discovery_service.start_discovery()

            # Keep the application running
            while self.main_window.isVisible():
                await asyncio.sleep(0.1)
                self.app.processEvents()  # Process Qt events

            # Cleanup before exit
            await self.cleanup()
            return 0

        except Exception as e:
            self.logger.error(f"Application error: {e}")
            await self.cleanup()
            QMessageBox.critical(None, "Error", str(e))
            return 1

def main():
    try:
        if not is_admin():
            if elevate():
                return
            sys.exit(1)
        
        app = Application()
        loop = app.loop
        
        try:
            exit_code = loop.run_until_complete(app.run())
            if exit_code == 0:
                loop.run_forever()
        except Exception as e:
            if hasattr(app, 'logger'):
                app.logger.error(f"Application failed: {e}")
            traceback.print_exc()
            return 1
        finally:
            try:
                loop.run_until_complete(app.cleanup())
            except Exception as e:
                print(f"Final cleanup error: {e}")
            loop.close()
            
    except SystemExit:
        raise
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Startup error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    main()
