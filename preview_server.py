"""Serve docs/ for preview_site.bat, telling the browser never to cache.

Python's plain http.server lets browsers reuse an old copy of a page, so a
freshly rebuilt demo can keep showing its previous version."""
import functools
import http.server
import sys
from pathlib import Path


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
    docs = Path(__file__).resolve().parent / "docs"
    handler = functools.partial(NoCacheHandler, directory=str(docs))
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()
