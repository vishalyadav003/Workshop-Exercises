"""Serve the helpdesk UI with Python's built-in web server."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).resolve().parent))
print("Helpdesk portal: http://localhost:5202")
ThreadingHTTPServer(("127.0.0.1", 5202), handler).serve_forever()
