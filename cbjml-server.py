#!/usr/bin/env python3
"""Static server with /api/update endpoint for live data refresh."""
import os, json, subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.environ.get("CBJML_ROOT", "/app")
PORT = int(os.environ.get("CBJML_PORT", "8102"))

class DashboardHandler(SimpleHTTPRequestHandler):
    directory = ROOT

    def end_headers(self):
        path = self.path.split("?")[0]
        if path.endswith((".html", "/")) or path == "/":
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header("Cache-Control", "public, max-age=3600, must-revalidate")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/update":
            self.handle_update()
        elif self.path == "/" or self.path == "/index.html":
            self.path = "/Dashboard_CBJML.html"
            super().do_GET()
        else:
            super().do_GET()

    def handle_update(self):
        """Run ETL sync and return result."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        try:
            env = os.environ.copy()
            result = subprocess.run(
                ["python3", "/app/etl_sync.py"],
                capture_output=True, text=True, timeout=60,
                cwd=ROOT, env=env
            )

            if result.returncode == 0:
                # Extract N from output
                n_families = "unknown"
                for line in result.stdout.split("\n"):
                    if "families" in line.lower() or "familias" in line.lower():
                        n_families = line.strip()
                        break

                response = {
                    "success": True,
                    "message": f"Dashboard actualizado - {n_families}",
                    "reload": True
                }
            else:
                response = {
                    "success": False,
                    "message": f"Error: {result.stderr[:200]}",
                    "reload": False
                }
        except subprocess.TimeoutExpired:
            response = {"success": False, "message": "Timeout: ETL took too long", "reload": False}
        except Exception as e:
            response = {"success": False, "message": str(e), "reload": False}

        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    def log_message(self, fmt, *args):
        print(f"[cbjml] {self.address_string()} {fmt % args}")

if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"serving {ROOT} on :{PORT} (with /api/update endpoint)")
    server.serve_forever()
