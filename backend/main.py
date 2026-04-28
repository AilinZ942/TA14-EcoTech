from __future__ import annotations

import secrets
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_wtf import CSRFProtect
from login import auth_bp
from location import location_bp
from optimizer import optimizer_bp



load_dotenv()

app = Flask(__name__)



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
        "origins": ["http://localhost:5173"],  # allow only the frontend origin
        "supports_credentials": True,  # 重要：允许携带 cookie
        "allow_headers": ["Content-Type", "X-CSRF-Token"]
    }
})

# Configure CSRF protection
csrf = CSRFProtect(app)
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_HEADERS'] = ['X-CSRF-Token']

app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(location_bp, url_prefix="/api/")
app.register_blueprint(optimizer_bp, url_prefix="/api/")







if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
