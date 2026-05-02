from __future__ import annotations
import os
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import generate_csrf
import logging

auth_bp = Blueprint("login", __name__)

USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "password")
PASSWORD_HASH = generate_password_hash(PASSWORD)
MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

login_attempts = defaultdict(list)




@auth_bp.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    return jsonify({'csrf_token': generate_csrf()})


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "not logged in", "code": 401}), 401
        return f(*args, **kwargs)

    return decorated_function


def is_locked_out(ip: str) -> bool:
    attempts = login_attempts[ip]
    # Remove attempts that are outside the lockout window
    cutoff = datetime.now() - LOCKOUT_DURATION
    login_attempts[ip] = [attempt for attempt in attempts if attempt > cutoff]
    return len(login_attempts[ip]) >= MAX_ATTEMPTS


def record_failed_attempt(ip: str) -> None:
    login_attempts[ip].append(datetime.now())


@auth_bp.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr

    if is_locked_out(ip):
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"too many login attempts, please try again in {LOCKOUT_DURATION.seconds // 60} minutes",
                }
            ),
            429,
        )

    data = request.get_json()


    if data.get('username')  == USERNAME and check_password_hash(PASSWORD_HASH, data.get('password')):
        login_attempts.pop(ip, None)
        session["logged_in"] = True
        session["ip"] = ip  # store IP in session for hijacking detection
        session.permanent = True # use permanent session to enable expiration
        return jsonify({"success": True, "message": "login successful"})

    record_failed_attempt(ip)
    remaining = MAX_ATTEMPTS - len(login_attempts[ip])
    return (
        jsonify(
            {
                "success": False,
                "message": f"Invalid username or password, {remaining} attempts remaining",
            }
        ),
        401,
    )


# logout
@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    session.pop('ip', None)
    return jsonify({'success': True, 'message': 'logout successful'})

# authentication check
@auth_bp.route('/check-auth', methods=['GET'])
def check_auth():
    return jsonify({'logged_in': session.get('logged_in', False)})


logging.basicConfig(
    filename='auth.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)



# detect session hijacking by checking IP address consistency
@auth_bp.before_request
def check_session_validity():
    if session.get('logged_in'):  
        original_ip = session.get("ip")
        current_ip = request.remote_addr

        if not original_ip or original_ip != current_ip:
            logging.warning(
                f"Session IP not match - Original IP: {original_ip}, Current IP: {current_ip}"
            )
            session.clear()
            return jsonify({"error": "Session has expired"}), 401  
