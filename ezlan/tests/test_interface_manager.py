import unittest
from ezlan.network.interface_manager import InterfaceManager

class TestInterfaceManager(unittest.TestCase):
    def setUp(self):
        self.interface_manager = InterfaceManager()

    def test_create_interface(self):
        result = self.interface_manager.create_interface()
        self.assertTrue(result)

    def test_cleanup_interface(self):
        result = self.interface_manager.cleanup_interface()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
