"""Browser dashboard for the reproducible environment and dependency audit."""
import importlib.metadata
import sys
from flask import Flask, jsonify, render_template
from src.validate_env import _required_distributions, REQUIRED_ENV, REQUIREMENTS, ROOT
from src.config import load_settings, validate_settings

app = Flask(__name__)

def snapshot():
    settings = load_settings()
    errors = validate_settings(settings)
    required = _required_distributions(REQUIREMENTS) if REQUIREMENTS.exists() else []
    dependencies = []
    for name in required:
        try:
            version = importlib.metadata.version(name)
            dependencies.append({"name": name, "version": version, "ok": True})
        except importlib.metadata.PackageNotFoundError:
            dependencies.append({"name": name, "version": "Not installed", "ok": False})
    return {"python": sys.version.split()[0], "python_ok": sys.version_info >= (3, 8),
            "environment": settings.app_env or "Not set", "app_name": settings.app_name or "Not set",
            "log_level": settings.log_level or "Not set", "token_configured": bool(settings.api_token and settings.api_token != "replace-with-a-local-placeholder"),
            "dependencies": dependencies, "errors": errors, "env_file": (ROOT / ".env").exists()}

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/status")
def status():
    return jsonify(snapshot())

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False, port=5201)
