import PyInstaller.__main__
import os
import shutil
import requests
from pathlib import Path
import sys

def download_tap_driver():
    urls = [
        "https://build.openvpn.net/downloads/releases/tap-windows-9.24.2-I601-Win10.exe",
        "https://swupdate.openvpn.org/community/releases/tap-windows-9.24.2-I601-Win10.exe",
        "https://github.com/OpenVPN/tap-windows6/releases/download/v9.24.2/tap-windows-9.24.2-I601-Win10.exe"
    ]
    
    resources_dir = Path("ezlan/resources")
    resources_dir.mkdir(exist_ok=True)
    tap_driver_path = resources_dir / "tap-windows.exe"
    
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(tap_driver_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception:
            continue
    return False

def build_executable():
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Download TAP driver
    if not download_tap_driver():
        print("Warning: Could not download TAP driver. Build will continue but runtime downloads may fail.")

    # PyInstaller command
    PyInstaller.__main__.run([
        'ezlan/main.py',
        '--name=EZLan',
        '--onefile',
        '--windowed',
        '--add-data=ezlan/resources;resources',
        '--hidden-import=PyQt6',
        '--hidden-import=cryptography',
        '--hidden-import=netifaces',
        '--hidden-import=ping3',
        '--hidden-import=scapy',
        '--hidden-import=pyqtgraph',
        '--hidden-import=numpy',
        '--uac-admin',
    ])

if __name__ == "__main__":
    build_executable()
