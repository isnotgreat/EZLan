import sys
import ctypes
import traceback
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication, QMessageBox
from ezlan.gui.main_window import MainWindow
from ezlan.network.discovery import DiscoveryService
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
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        if ret <= 32:  # Error codes from ShellExecuteW
            raise RuntimeError(f"Failed to elevate privileges (error code: {ret})")
        return True
    except Exception as e:
        print(f"Failed to get admin rights: {e}")
        input("Press Enter to exit...")
        return False

async def async_main(app):
    logger = Logger("Main")
    
    # Check and setup system requirements
    try:
        installer = SystemInstaller()
        installer.check_and_setup()
    except Exception as e:
        QMessageBox.critical(None, "Setup Error", 
            f"Failed to setup required components: {str(e)}\n"
            "Please run the application as administrator and ensure you have internet connectivity.")
        return 1
    
    try:
        # Initialize network services
        discovery_service = DiscoveryService()
        tunnel_service = TunnelService()
        
        # Create and show main window
        window = MainWindow(discovery_service, tunnel_service)
        window.show()
        
        try:
            # Start discovery service after window is shown
            discovery_service.start_discovery()
        except Exception as e:
            logger.warning(f"Discovery service failed to start: {e}")
            
        return 0
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        QMessageBox.critical(None, "Startup Error", 
            f"Failed to start application: {str(e)}")
        return 1

def main():
    try:
        if not is_admin():
            if not elevate():
                return 1
            return 0

        # Create the application first
        app = QApplication(sys.argv)
        
        # Create event loop after QApplication
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Run the async main
        exit_code = loop.run_until_complete(async_main(app))
        
        if exit_code == 0:
            # Start the event loop
            sys.exit(app.exec())
        else:
            sys.exit(exit_code)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        print("\nStack trace:")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
