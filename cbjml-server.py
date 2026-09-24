#!/usr/bin/env python3
"""Servidor estático CBJML con actualización ETL serializada."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(os.environ.get("CBJML_ROOT", "/app")).resolve()
PORT = int(os.environ.get("CBJML_PORT", "8102"))
ETL_PATH = ROOT / "etl_sync.py"
PIPELINE_LOCK = threading.Lock()
PUBLIC_ASSETS = {"/Dashboard_CBJML.html", "/dashboard_runtime.js"}


def is_public_asset(path: str) -> bool:
    return path in {"/", "/index.html", *PUBLIC_ASSETS}


def run_etl() -> subprocess.CompletedProcess[str]:
    """Ejecuta el mismo pipeline para arranque y actualización manual."""
    env = os.environ.copy()
    env["CBJML_ROOT"] = str(ROOT)
    with PIPELINE_LOCK:
        return subprocess.run(
            [sys.executable, str(ETL_PATH)],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=ROOT,
            env=env,
        )


def read_snapshot_count() -> int | None:
    path = ROOT / "dashboard_data.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return len(payload.get("responses", []))
    except (OSError, ValueError, TypeError):
        return None


class DashboardHandler(SimpleHTTPRequestHandler):
    directory = str(ROOT)

    def end_headers(self):
        path = urlsplit(self.path).path
        if path.endswith((".html", "/")) or path == "/":
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        else:
            self.send_header("Cache-Control", "public, max-age=3600, must-revalidate")
        super().end_headers()

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        path = urlsplit(self.path).path
        if path in {"/api/health", "/api/update"}:
            self.send_json(200, {"ok": True})
        elif is_public_asset(path):
            if path in {"/", "/index.html"}:
                self.path = "/Dashboard_CBJML.html"
            super().do_HEAD()
        else:
            self.send_json(404, {"ok": False})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/update":
            self.handle_update()
        elif path == "/api/health":
            self.send_json(200, {"ok": True, "families": read_snapshot_count()})
        elif not is_public_asset(path):
            self.send_json(404, {"ok": False})
        elif path in {"/", "/index.html"}:
            self.path = "/Dashboard_CBJML.html"
            super().do_GET()
        else:
            super().do_GET()

    def handle_update(self):
        try:
            result = run_etl()
        except subprocess.TimeoutExpired:
            self.send_json(504, {"success": False, "message": "Timeout: ETL tardó demasiado", "reload": False})
            return
        except Exception as error:
            self.send_json(500, {"success": False, "message": str(error), "reload": False})
            return
        if result.returncode != 0:
            self.send_json(502, {"success": False, "message": result.stderr.strip()[:500] or "ETL falló", "reload": False})
            return
        count = read_snapshot_count()
        self.send_json(200, {"success": True, "message": f"Dashboard actualizado: {count if count is not None else 'N'} familias", "reload": True})

    def log_message(self, fmt, *args):
        print(f"[cbjml] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    os.chdir(ROOT)
    try:
        startup_result = run_etl()
        if startup_result.returncode == 0:
            print(f"ETL on startup: {startup_result.stdout.strip()}")
        else:
            print(f"ETL on startup failed: {startup_result.stderr.strip()[:500]}")
    except Exception as error:
        print(f"ETL on startup error: {error}")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"serving {ROOT} on :{PORT} (ETL serializado)")
    server.serve_forever()
