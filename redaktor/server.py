"""Serve only the editor and its approved assets, not the repository."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import os

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = {
    '/redaktor/': 'redaktor/index.html',
    '/redaktor/index.html': 'redaktor/index.html',
    '/redaktor/style.css': 'redaktor/style.css',
    '/redaktor/app.js': 'redaktor/app.js',
    '/redaktor/oblozhka-zhivaya.png': 'redaktor/oblozhka-zhivaya.png',
    **{f'/proekt/07-upakovka-soobshchestva/ramka-vybor-0{i}.png':
       f'proekt/07-upakovka-soobshchestva/ramka-vybor-0{i}.png' for i in range(1, 6)},
}

class Handler(SimpleHTTPRequestHandler):
    def _serve(self, head=False):
        path = unquote(urlsplit(self.path).path)
        if path in ('/', '/redaktor'):
            self.send_response(302)
            self.send_header('Location', '/redaktor/')
            self.end_headers()
            return
        relative = PUBLIC.get(path)
        target = (ROOT / relative).resolve() if relative else None
        if not target or not target.is_relative_to(ROOT) or not target.is_file():
            self.send_error(404, 'Not found')
            return
        self._target = target
        if head:
            super().do_HEAD()
        else:
            super().do_GET()

    def translate_path(self, path):
        return str(self._target)

    def do_GET(self):
        self._serve()

    def do_HEAD(self):
        self._serve(head=True)

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8000'))), Handler).serve_forever()
