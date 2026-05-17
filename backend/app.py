from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import os

from flask import Flask
from flask_wtf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from utils.env import load_backend_env


BACKEND_ROOT_DIR = Path(__file__).resolve().parent
load_backend_env(BACKEND_ROOT_DIR)

# Import blueprints only after loading .env so route modules can read env values safely.
from routes.health import health_bp  # noqa: E402
from routes.login import auth_bp  # noqa: E402
from routes.location import location_bp  # noqa: E402
from routes.optimizer import optimizer_bp  # noqa: E402
from routes.repair_check import repair_check_bp  # noqa: E402
from routes.emissions import emissions_bp  # noqa: E402


app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-this"),
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SESSION_REFRESH_EACH_REQUEST=True,
)

# Configure CSRF protection
csrf = CSRFProtect(app)
app.config["WTF_CSRF_CHECK_DEFAULT"] = False
app.config["WTF_CSRF_HEADERS"] = ["X-CSRF-Token"]

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(location_bp, url_prefix="/api")
app.register_blueprint(optimizer_bp, url_prefix="/api")
app.register_blueprint(repair_check_bp, url_prefix="/api")
app.register_blueprint(emissions_bp, url_prefix="/api")


@app.route("/api/healthcheck", methods=["GET"])
def healthcheck():
    return {"status": "ok", "service": "ecotech-backend"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
