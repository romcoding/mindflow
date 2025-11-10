from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from src.models.user import User, db
from sqlalchemy.exc import OperationalError, SQLAlchemyError
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
        # Accept either 'username' or 'name' field, generate username if needed
        if not data.get('email') or not data.get('password'):
            audit_log("register", data.get("email") or data.get("name"), "fail", "missing email or password")
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email and password first (before database queries)
        if not validate_email(email):
            audit_log("register", email, "fail", "invalid email format")
            return jsonify({'error': 'Invalid email format'}), 400
        is_valid, message = validate_password(password)
        if not is_valid:
            audit_log("register", email, "fail", message)
            return jsonify({'error': message}), 400
        
        # Check database connection before proceeding
        try:
            # Test database connection by attempting a simple query
            User.query.limit(1).all()
        except (OperationalError, SQLAlchemyError) as db_error:
            audit_log("register", email, "fail", f"database connection error: {str(db_error)}")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database. Please try again in a moment.'
            }), 503
        
        # Generate username from name if provided, otherwise from email
        if data.get('username'):
            username = data['username'].strip()
        elif data.get('name'):
            # Extract username from full name (first part before space, lowercase, alphanumeric only)
            name_parts = data['name'].strip().split()
            username_base = re.sub(r'[^a-zA-Z0-9]', '', name_parts[0].lower()) if name_parts else ''
            if not username_base:
                username_base = email.split('@')[0]
            # Ensure username is unique
            username = username_base
            counter = 1
            max_attempts = 100  # Prevent infinite loop
            while counter < max_attempts and User.query.filter_by(username=username).first():
                username = f"{username_base}{counter}"
                counter += 1
        else:
            # Generate from email
            username = email.split('@')[0]
            counter = 1
            max_attempts = 100  # Prevent infinite loop
            while counter < max_attempts and User.query.filter_by(username=username).first():
                username = f"{email.split('@')[0]}{counter}"
                counter += 1
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            audit_log("register", email, "fail", "username exists")
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=email).first():
            audit_log("register", email, "fail", "email exists")
            return jsonify({'error': 'Email already registered'}), 400
        # Extract first_name and last_name from name if provided
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        if not first_name and data.get('name'):
            # Split name into first and last
            name_parts = data['name'].strip().split()
            if len(name_parts) > 0:
                first_name = name_parts[0]
            if len(name_parts) > 1:
                last_name = ' '.join(name_parts[1:])
        
        user = User(
            username=username,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Create JWT with additional user claims (blended approach)
        additional_claims = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        access_token = create_access_token(
            identity=user.id, 
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(days=30)
        )
        audit_log("register", email, "success", None)
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
    except (OperationalError, SQLAlchemyError) as db_error:
        db.session.rollback()
        error_message = str(db_error)
        print(f"Database error during registration for {data.get('email')}: {error_message}")
        import traceback
        print(traceback.format_exc())
        audit_log("register", data.get("email") or data.get("name"), "fail", f"database error: {error_message}")
        return jsonify({
            'error': 'Database error',
            'message': 'Unable to complete registration due to database error. Please try again.'
        }), 503
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        print(f"Registration failed for {data.get('email')}: {error_message}")
        import traceback
        print(traceback.format_exc())
        audit_log("register", data.get("email") or data.get("name"), "fail", error_message)
        # Return more detailed error for debugging
        return jsonify({
            'error': 'Registration failed',
            'message': error_message,
            'details': error_message
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        # Accept either 'username' or 'email' field
        identifier = data.get('username') or data.get('email')
        if not identifier or not data.get('password'):
            audit_log("login", identifier or "unknown", "fail", "missing username/email or password")
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        identifier = identifier.strip()
        password = data['password']
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()
        if not user or not user.check_password(password):
            audit_log("login", identifier, "fail", "invalid credentials")
            return jsonify({'error': 'Invalid credentials'}), 401
        if not user.is_active:
            audit_log("login", identifier, "fail", "account deactivated")
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Create JWT with additional user claims (blended approach)
        additional_claims = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(days=30)
        )
        audit_log("login", identifier, "success", None)
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
    except Exception as e:
        audit_log("login", data.get("username"), "fail", str(e))
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Create new access token with updated user claims
        additional_claims = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip() if data['first_name'] else None
        if 'last_name' in data:
            user.last_name = data['last_name'].strip() if data['last_name'] else None
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                if not validate_email(new_email):
                    return jsonify({'error': 'Invalid email format'}), 400
                if User.query.filter(User.email == new_email, User.id != user.id).first():
                    return jsonify({'error': 'Email already registered'}), 400
                user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old password and new password are required'}), 400
        
        if not user.check_password(old_password):
            audit_log("change_password", user.email, "fail", "incorrect old password")
            return jsonify({'error': 'Incorrect old password'}), 400
        
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        audit_log("change_password", user.email, "success", None)
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500
