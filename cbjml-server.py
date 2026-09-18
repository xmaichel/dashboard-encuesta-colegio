#!/usr/bin/env python3
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.environ.get("CBJML_ROOT", "/app")
PORT = int(os.environ.get("CBJML_PORT", "8102"))

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?")[0]
        if path.endswith((".html", "/")) or path == "/":
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header("Cache-Control", "public, max-age=3600, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[cbjml] {self.address_string()} {fmt % args}")

if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), NoCacheHandler)
    print(f"serving {ROOT} on :{PORT} (no-store HTML)")
    server.serve_forever()
