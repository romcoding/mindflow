from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from src.models.user import User, db
from src.extensions import limiter
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import text
from datetime import timedelta
import re
import logging
import json
import os
import secrets
import requests
import base64
from datetime import datetime
from urllib.parse import quote

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

def ensure_db_connection(max_retries=2):
    """Ensure database connection is available with retry logic.
    Render PostgreSQL databases on free tier sleep after inactivity."""
    for retry in range(max_retries):
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return True
        except (OperationalError, SQLAlchemyError) as db_error:
            if retry < max_retries - 1:
                # Wait before retrying (database might be waking up)
                # Reduced wait time for faster response
                import time
                time.sleep(0.3 * (retry + 1))  # 0.3s, 0.6s (faster than before)
                # Try to refresh the connection
                try:
                    db.session.rollback()
                except:
                    pass
                continue
            else:
                # Final attempt failed
                error_msg = str(db_error)
                logging.error(f"Database connection failed after {max_retries} attempts: {error_msg[:200]}")
                return False
    return False

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.get_json()
        if not data:
            audit_log("register", "unknown", "fail", "no JSON data received")
            return jsonify({'error': 'Invalid request: No data received'}), 400
        
        logging.info(f"Registration attempt for email: {data.get('email', 'unknown')}")
        
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
        
        # Check database connection before proceeding with retry logic
        # Render PostgreSQL databases on free tier sleep after inactivity and need a moment to wake up
        # Reduce retries for faster response - database should be awake by now
        if not ensure_db_connection(max_retries=2):
            audit_log("register", email, "fail", "database connection failed after retries")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database. The database might be waking up. Please try again in a few seconds.'
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
        # Log JWT config before creating token
        from flask import current_app
        logging.info(f"Creating access token for user {user.id} with JWT_SECRET_KEY length: {len(current_app.config.get('JWT_SECRET_KEY', ''))}")
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
        logging.info(f"Token created successfully, length: {len(access_token)}")
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
        if not data:
            audit_log("login", "unknown", "fail", "no JSON data received")
            return jsonify({'error': 'Invalid request: No data received'}), 400
        
        logging.info(f"Login attempt for identifier: {data.get('username') or data.get('email', 'unknown')}")
        
        # Accept either 'username' or 'email' field
        identifier = data.get('username') or data.get('email')
        if not identifier or not data.get('password'):
            audit_log("login", identifier or "unknown", "fail", "missing username/email or password")
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        # Check database connection before proceeding
        # Use fewer retries for login to speed it up
        if not ensure_db_connection(max_retries=2):
            audit_log("login", identifier, "fail", "database connection failed")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database. The database might be waking up. Please try again in a few seconds.'
            }), 503
        
        identifier = identifier.strip()
        password = data['password']
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()
        
        # Check if user exists
        if not user:
            audit_log("login", identifier, "fail", "user not found")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is OAuth-only (no password)
        if user.oauth_provider and not user.password_hash:
            audit_log("login", identifier, "fail", "oauth-only account")
            return jsonify({
                'error': 'This account was created with OAuth. Please sign in with your OAuth provider.',
                'oauth_provider': user.oauth_provider
            }), 401
        
        # Check password
        if not user.check_password(password):
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
        # Log JWT config before creating token
        from flask import current_app
        logging.info(f"Creating access token for user {user.id} with JWT_SECRET_KEY length: {len(current_app.config.get('JWT_SECRET_KEY', ''))}")
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
        logging.info(f"Token created successfully, length: {len(access_token)}")
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

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')

# Get frontend URL for redirects
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

def generate_state():
    """Generate a secure random state for OAuth"""
    return secrets.token_urlsafe(32)

@auth_bp.route('/oauth/<provider>/authorize', methods=['GET'])
@limiter.limit("10 per minute")
def oauth_authorize(provider):
    """Initiate OAuth flow - redirects to provider"""
    try:
        # Generate secure state token
        state = generate_state()
        session[f'oauth_{provider}_state'] = state
        
        if provider == 'google':
            if not GOOGLE_CLIENT_ID:
                return jsonify({'error': 'Google OAuth not configured'}), 500
            
            # Use request.url_root to get the full base URL
            base_url = request.url_root.rstrip('/')
            redirect_uri = f"{base_url}/api/auth/oauth/google/callback"
            scope = 'openid email profile'
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={GOOGLE_CLIENT_ID}&"
                f"redirect_uri={redirect_uri}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"state={state}&"
                f"access_type=online"
            )
            return redirect(auth_url)
        
        elif provider == 'github':
            if not GITHUB_CLIENT_ID:
                return jsonify({'error': 'GitHub OAuth not configured'}), 500
            
            # Use request.url_root to get the full base URL
            base_url = request.url_root.rstrip('/')
            redirect_uri = f"{base_url}/api/auth/oauth/github/callback"
            scope = 'user:email'
            auth_url = (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={GITHUB_CLIENT_ID}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}&"
                f"state={state}"
            )
            return redirect(auth_url)
        
        else:
            return jsonify({'error': 'Unsupported OAuth provider'}), 400
    
    except Exception as e:
        logging.error(f"OAuth authorization error: {str(e)}")
        return jsonify({'error': 'OAuth authorization failed', 'details': str(e)}), 500

@auth_bp.route('/oauth/<provider>/callback', methods=['GET'])
@limiter.limit("20 per minute")
def oauth_callback(provider):
    """Handle OAuth callback from provider"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            error_msg = quote(error, safe='')
            return redirect(f"{FRONTEND_URL}?error={error_msg}")
        
        # Verify state
        stored_state = session.get(f'oauth_{provider}_state')
        if not stored_state or stored_state != state:
            return redirect(f"{FRONTEND_URL}?error=invalid_state")
        
        # Clear state from session
        session.pop(f'oauth_{provider}_state', None)
        
        if not code:
            return redirect(f"{FRONTEND_URL}?error=no_code")
        
        # Exchange code for access token
        if provider == 'google':
            token_url = 'https://oauth2.googleapis.com/token'
            base_url = request.url_root.rstrip('/')
            token_data = {
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': f"{base_url}/api/auth/oauth/google/callback",
                'grant_type': 'authorization_code'
            }
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens.get('access_token')
            
            # Get user info from Google
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Extract user data
            email = user_info.get('email')
            first_name = user_info.get('given_name')
            last_name = user_info.get('family_name')
            provider_id = user_info.get('id')
            avatar_url = user_info.get('picture')
            username = user_info.get('name', email.split('@')[0] if email else 'user')
            
        elif provider == 'github':
            token_url = 'https://github.com/login/oauth/access_token'
            base_url = request.url_root.rstrip('/')
            token_data = {
                'code': code,
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'redirect_uri': f"{base_url}/api/auth/oauth/github/callback"
            }
            headers = {'Accept': 'application/json'}
            token_response = requests.post(token_url, data=token_data, headers=headers)
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens.get('access_token')
            
            # Get user info from GitHub
            user_info_url = 'https://api.github.com/user'
            headers = {'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}
            user_response = requests.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_info = user_response.json()
            
            # Get email (may need separate call)
            email = user_info.get('email')
            if not email:
                # Try to get primary email
                emails_url = 'https://api.github.com/user/emails'
                emails_response = requests.get(emails_url, headers=headers)
                if emails_response.status_code == 200:
                    emails = emails_response.json()
                    primary_email = next((e for e in emails if e.get('primary')), emails[0] if emails else None)
                    email = primary_email.get('email') if primary_email else None
            
            # Extract user data
            name = user_info.get('name', '')
            name_parts = name.split() if name else []
            first_name = name_parts[0] if name_parts else None
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            provider_id = str(user_info.get('id'))
            avatar_url = user_info.get('avatar_url')
            username = user_info.get('login', email.split('@')[0] if email else 'user')
        
        else:
            return redirect(f"{FRONTEND_URL}?error=unsupported_provider")
        
        if not email:
            return redirect(f"{FRONTEND_URL}?error=no_email")
        
        # Find or create user
        user = User.find_or_create_oauth_user(
            provider=provider,
            provider_id=provider_id,
            email=email.lower(),
            username=username,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url
        )
        
        if not user.is_active:
            return redirect(f"{FRONTEND_URL}?error=account_deactivated")
        
        # Create JWT tokens
        additional_claims = {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        access_token_jwt = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(hours=24)
        )
        refresh_token_jwt = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims,
            expires_delta=timedelta(days=30)
        )
        
        audit_log("oauth_login", email, "success", f"provider={provider}")
        
        # Redirect to frontend with tokens in URL fragment (more secure than query params)
        # Frontend will extract tokens and store them
        tokens_encoded = base64.urlsafe_b64encode(
            json.dumps({
                'access_token': access_token_jwt,
                'refresh_token': refresh_token_jwt,
                'user': user.to_dict()
            }).encode()
        ).decode()
        
        # URL encode the token to handle special characters
        tokens_encoded = quote(tokens_encoded, safe='')
        return redirect(f"{FRONTEND_URL}?token={tokens_encoded}")
    
    except requests.RequestException as e:
        logging.error(f"OAuth callback request error: {str(e)}")
        error_msg = quote("oauth_request_failed", safe='')
        return redirect(f"{FRONTEND_URL}?error={error_msg}")
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        error_msg = quote("oauth_callback_failed", safe='')
        return redirect(f"{FRONTEND_URL}?error={error_msg}")
