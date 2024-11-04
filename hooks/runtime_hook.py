import os
import sys
import atexit
import subprocess

class DummyStream:
    def write(self, *args, **kwargs):
        pass
    def flush(self, *args, **kwargs):
        pass
    def close(self):
        pass

# Register cleanup function
atexit.register(lambda: None)

# Replace standard streams with dummy ones
if hasattr(sys, '_MEIPASS'):
    sys.stdin = DummyStream()
    sys.stdout = DummyStream()
    sys.stderr = DummyStream()

    # Set environment variables
    os.environ['EZLAN_RESOURCES'] = os.path.join(sys._MEIPASS, 'resources')
    os.environ['EZLAN_CONFIG'] = os.path.join(sys._MEIPASS, 'config')