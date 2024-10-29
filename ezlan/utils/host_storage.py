import json
import os
from pathlib import Path
from ezlan.utils.logger import Logger

class HostStorage:
    def __init__(self):
        self.logger = Logger("HostStorage")
        self.hosts = {}
        self.storage_path = Path.home() / '.ezlan' / 'hosts.json'
        self._load_hosts()

    def _load_hosts(self):
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    self.hosts = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load hosts: {e}")
            self.hosts = {}

    def _save_hosts(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.hosts, f)
        except Exception as e:
            self.logger.error(f"Failed to save hosts: {e}")

    def add_host(self, ip: str, port: int, password: str):
        self.hosts[f"{ip}:{port}"] = {
            'ip': ip,
            'port': port,
            'password': password
        }
        self._save_hosts()

    def remove_host(self, ip: str, port: int):
        key = f"{ip}:{port}"
        if key in self.hosts:
            del self.hosts[key]
            self._save_hosts()

    def get_hosts(self):
        return self.hosts 