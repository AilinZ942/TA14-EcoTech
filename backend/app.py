from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_wtf import CSRFProtect
from routes.health import health_bp
from routes.login import auth_bp
from routes.location import location_bp
from routes.optimizer import optimizer_bp
from routes.emissions import emissions_bp
from werkzeug.middleware.proxy_fix import ProxyFix



BACKEND_ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_ROOT_DIR / ".env.local")

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

app.config.update(
    SECRET_KEY=secrets.token_hex(32),
    SESSION_COOKIE_SECURE=True,      # only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True,    # prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE='Strict', # strict same-site policy to prevent CSRF
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),  # session expires after 12 hours
    SESSION_REFRESH_EACH_REQUEST=True  # refresh session on each request to extend lifetime
)



CORS(app, resources={
    r"/api/*": {
        "origins": [
            os.environ.get("FRONTEND_URL", "http://localhost:5173")
        ],  # allow local Vite preview ports
        "supports_credentials": True,  # important: allow credentials (cookies)
        "allow_headers": ["Content-Type", "X-CSRF-Token"]
    }
})

# Configure CSRF protection
csrf = CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_HEADERS'] = ['X-CSRF-Token']

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(location_bp, url_prefix="/api")
app.register_blueprint(optimizer_bp, url_prefix="/api")
app.register_blueprint(emissions_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
