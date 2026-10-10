"""Serve the analytics dashboard using Python's standard library."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
print("Dashboard: http://localhost:5402")
ThreadingHTTPServer(("127.0.0.1", 5402), handler).serve_forever()
