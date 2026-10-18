import unittest
import threading
from network import *

IP_ADDRESS = "192.168.1.148"
PORT = 8888

class NetworkTests(unittest.TestCase):
    """Server-client behaviour test class."""

    def setUp(self):
        self.network = Network(IP_ADDRESS, PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((IP_ADDRESS, PORT))
        self.server.listen(1)

        self.server_thread = threading.Thread(target=self.network.connect(), daemon=True)
        self.server_thread.start()

    def tearDownClass(self):
        self.server.close()

    def test_client_connection(self):
        try:
            self.network.client.connect((IP_ADDRESS, PORT))
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Client failed to connect: {e}")
        finally:
            self.network.client.close()
    
