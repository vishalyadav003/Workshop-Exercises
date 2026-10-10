"""Flask entry point for the campus lost-and-found notice board."""
import logging
import os
from pathlib import Path

from flask import Flask, render_template

from routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-this-key"),
        DATA_FILE=os.environ.get("NOTICE_DATA_FILE", str(Path(__file__).parent / "data" / "notices.json")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    log_path = Path(__file__).parent / "logs"
    log_path.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_path / "app.log", encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    app.logger.addHandler(handler)

    app.register_blueprint(bp)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="We couldn’t find that page or notice."), 404

    @app.errorhandler(500)
    def server_error(_error):
        app.logger.exception("Unhandled server error")
        return render_template("error.html", code=500, message="Something went wrong. Please try again later."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5401, debug=os.environ.get("FLASK_DEBUG") == "1")
