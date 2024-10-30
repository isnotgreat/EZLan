import PyInstaller.__main__
import os
import shutil
import requests
from pathlib import Path
import sys


def build_executable():
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")


    # PyInstaller command
    PyInstaller.__main__.run([
        'ezlan/main.py',
        '--name=EZLan',
        '--onefile',
        '--windowed',
        '--icon=ezlan/resources/icon.ico',
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
