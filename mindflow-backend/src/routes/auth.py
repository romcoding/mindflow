from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from src.models.user import User, db
from datetime import timedelta
import re
import logging
import json
from datetime import datetime

# Setup logger just once (module level)
audit_logger = logging.getLogger("auth_audit")
if not audit_logger.handlers:
    handler = logging.FileHandler("auth_audit.log")
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)
    audit_logger.setLevel(logging.INFO)

def audit_log(event_type, username_or_email, result, reason=None):
    event = {
        "event": event_type,
        "user": username_or_email,
        "ip": request.remote_addr or None,
        "result": result,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    audit_logger.info(json.dumps(event))

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                audit_log("register", data.get("email") or data.get("username"), "fail", f"missing {field}")
                return jsonify({'error': f'{field} is required'}), 400
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        if not validate_email(email):
            audit_log("register", email, "fail", "invalid email format")
            return jsonify({'error': 'Invalid email format'}), 400
        is_valid, message = validate_password(password)
        if not is_valid:
            audit_log("register", email, "fail", message)
            return jsonify({'error': message}), 400
        if User.query.filter_by(username=username).first():
            audit_log("register", email, "fail", "username exists")
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=email).first():
            audit_log("register", email, "fail", "email exists")
            return jsonify({'error': 'Email already registered'}), 400
        user = User(
            username=username,
            email=email,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip()
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
        refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))
        audit_log("register", email, "success", None)
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except Exception as e:
        db.session.rollback()
        audit_log("register", data.get("email") or data.get("username"), "fail", str(e))
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data.get('username') or not data.get('password'):
            audit_log("login", data.get("username"), "fail", "missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400
        username = data['username'].strip()
        password = data['password']
        user = User.query.filter((User.username == username) | (User.email == username.lower())).first()
        if not user or not user.check_password(password):
            audit_log("login", username, "fail", "invalid credentials")
            return jsonify({'error': 'Invalid credentials'}), 401
        if not user.is_active:
            audit_log("login", username, "fail", "account deactivated")
            return jsonify({'error': 'Account is deactivated'}), 401
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
        refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))
        audit_log("login", username, "success", None)
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
    except Exception as e:
        audit_log("login", data.get("username"), "fail", str(e))
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

# In demo/no-auth mode you might not need the following endpoints; keeping them simple
@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    return jsonify({'error': 'Not implemented in demo mode'}), 400

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    return jsonify({'error': 'Not implemented in demo mode'}), 400

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    return jsonify({'error': 'Not implemented in demo mode'}), 400

@auth_bp.route('/change-password', methods=['PUT'])
def change_password():
    return jsonify({'error': 'Not implemented in demo mode'}), 400
