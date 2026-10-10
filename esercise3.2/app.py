"""Serve the feedback UI with Python's standard library."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
print("Feedback dashboard: http://localhost:5302")
ThreadingHTTPServer(("127.0.0.1", 5302), handler).serve_forever()
