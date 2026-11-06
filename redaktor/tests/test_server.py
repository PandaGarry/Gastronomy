import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer
from redaktor.server import Handler

class QuietHandler(Handler):
    def log_message(self, *args):
        pass

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def request(self, method, path):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path)
            response = connection.getresponse()
            body = response.read()
            return response.status, body
        finally:
            connection.close()

    def test_public_assets_and_head(self):
        self.assertEqual(self.request('GET', '/')[0], 302)
        self.assertEqual(self.request('GET', '/redaktor/')[0], 200)
        self.assertEqual(self.request('HEAD', '/redaktor/app.js')[0], 200)
        for i in range(1, 6):
            self.assertEqual(self.request('GET', f'/proekt/07-upakovka-soobshchestva/ramka-vybor-0{i}.png')[0], 200)

    def test_private_and_traversal_denied(self):
        for path in ['/proekt/01-strategiya/PROEKT.md', '/.git/config', '/redaktor/../README.md', '/redaktor/%2e%2e/README.md', '/proekt/', '/redaktor/server.py']:
            for method in ['GET', 'HEAD']:
                self.assertEqual(self.request(method, path)[0], 404, (method, path))

if __name__ == '__main__':
    unittest.main()
