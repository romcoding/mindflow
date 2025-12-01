import os
import sys
import time
import threading
import logging
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from src.models.db import db, bcrypt
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.tasks import tasks_bp
from src.routes.stakeholders import stakeholders_bp
from src.routes.notes import notes_bp
from src.routes.enhanced_tasks import enhanced_tasks_bp
from src.routes.stakeholder_relationships import stakeholder_relationships_bp, stakeholder_interactions_bp
from src.routes.admin import admin_bp
from datetime import timedelta
from src.extensions import limiter
from flask_limiter.util import get_remote_address
from src.models.user import User
# from src.models.organization import Organization  # Temporarily disabled
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.enhanced_task import EnhancedTask, TaskCategory
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
# Session configuration for OAuth state management
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows OAuth redirects

# Initialize extensions
jwt = JWTManager(app)
bcrypt.init_app(app)

# Rate Limiting setup (no app context at import time)
if os.environ.get('REDIS_URL'):
    limiter.storage_uri = os.environ['REDIS_URL']
else:
    limiter.storage_uri = 'memory://'
limiter.init_app(app)

# CORS configuration - allow configurable origins (defaults to allow all)
allowed_origins_env = os.environ.get('ALLOWED_ORIGINS')
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',') if origin.strip()]
    supports_credentials = os.environ.get('ALLOW_CREDENTIALS', 'false').lower() == 'true'
    logger.info(f"CORS allowed origins (env): {allowed_origins} | supports_credentials={supports_credentials}")
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=supports_credentials,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        max_age=86400
    )
else:
    # Allow all origins by default (no cookies used, tokens handled in headers)
    logger.info("CORS: allowing all origins (no ALLOWED_ORIGINS env set)")
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
        max_age=86400,
        supports_credentials=False  # Explicitly set to False for token-based auth
    )

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tasks_bp, url_prefix='/api')
app.register_blueprint(stakeholders_bp, url_prefix='/api')
app.register_blueprint(notes_bp, url_prefix='/api')
app.register_blueprint(enhanced_tasks_bp, url_prefix='/api')
app.register_blueprint(stakeholder_relationships_bp, url_prefix='/api')
app.register_blueprint(stakeholder_interactions_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Production: Use PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Parse and configure SSL settings for Render PostgreSQL
    # Render PostgreSQL requires SSL but sometimes has connection issues
    # Try prefer first, then require if prefer doesn't work
    if 'sslmode=' not in database_url:
        separator = '&' if '?' in database_url else '?'
        # Use 'prefer' instead of 'require' - it will use SSL if available but won't fail if there are issues
        database_url = f"{database_url}{separator}sslmode=prefer"
    elif 'sslmode=require' in database_url:
        # Replace require with prefer for better compatibility
        database_url = database_url.replace('sslmode=require', 'sslmode=prefer')

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    logger.info("Database URL configured (SSL mode: prefer)")
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    logger.info("Using SQLite database for development")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
engine_options = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': int(os.environ.get('SQLALCHEMY_POOL_RECYCLE_SECONDS', 300)),  # Recycle connections after 5 minutes
    'pool_size': int(os.environ.get('SQLALCHEMY_POOL_SIZE', 5)),  # Number of connections to maintain
    'max_overflow': int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 10)),  # Max connections beyond pool_size
    'echo': False,  # Set to True for SQL query logging
}

# Add connection timeout and SSL settings for PostgreSQL
if database_url and 'postgresql' in database_url:
    engine_options['connect_args'] = {
        'connect_timeout': 20,  # Increased timeout
        'sslmode': 'prefer',  # Prefer SSL but don't require it strictly
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
    }
    logger.info("PostgreSQL connection args configured with SSL prefer mode")

app.config['SQLALCHEMY_ENGINE_OPTIONS'].update(engine_options)
db.init_app(app)

# Import all models to ensure they're registered
from src.models.user import User
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction
from src.models.enhanced_task import EnhancedTask

def initialize_database(max_retries=15, base_delay_seconds=5):
    """Create database tables with retry logic. Non-blocking - allows app to start even if DB is unavailable."""
    db_initialized = False
    
    for attempt in range(1, max_retries + 1):
        try:
            with app.app_context():
                # Test connection first
                db.session.execute(text('SELECT 1'))
                # Then create tables
                db.create_all()
                logger.info("Database initialized successfully")
                db_initialized = True
                break
        except OperationalError as exc:
            error_msg = str(exc)
            logger.warning(
                "Database initialization failed (attempt %s/%s): %s. Will retry...",
                attempt,
                max_retries,
                error_msg[:200],  # Truncate long error messages
            )
            if attempt < max_retries:
                # Exponential backoff with jitter
                delay = base_delay_seconds * (2 ** (attempt - 1)) + (time.time() % 1)
                logger.info(f"Waiting {delay:.1f} seconds before retry...")
                time.sleep(delay)
            else:
                logger.error(
                    "Database initialization failed after %s attempts. "
                    "App will start but database operations may fail until connection is established. "
                    "This might be a temporary network issue. The app will retry on first request.",
                    max_retries
                )
        except Exception as exc:
            logger.exception("Unexpected error during database initialization")
            if attempt < max_retries:
                time.sleep(base_delay_seconds * attempt)
            # Don't raise - allow app to start
    
    return db_initialized

# Initialize database in background thread to avoid blocking app startup
def initialize_database_async():
    """Initialize database asynchronously to avoid blocking app startup."""
    def init_thread():
        time.sleep(2)  # Give the app a moment to fully start
        initialize_database()
    
    thread = threading.Thread(target=init_thread, daemon=True)
    thread.start()
    logger.info("Database initialization started in background thread")

# Try to initialize immediately, but don't block if it fails
try:
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully on startup")
except Exception as e:
    logger.warning("Database not immediately available, will retry in background: %s", str(e)[:200])
    # Start background initialization
    initialize_database_async()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        with app.app_context():
            db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)[:100]}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Security headers middleware
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Only add HSTS in production with HTTPS
    if os.environ.get('ENABLE_HSTS', 'false').lower() == 'true':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Request logging middleware
@app.before_request
def log_request_info():
    """Log all incoming requests for debugging"""
    # Skip logging for health checks and static files
    if request.path in ['/health', '/favicon.ico', '/robots.txt']:
        return
    logger.info(f"[{request.method}] {request.path} - Origin: {request.headers.get('Origin', 'N/A')} - IP: {request.remote_addr}")
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            # Sanitize request body to remove sensitive data before logging
            body = request.get_data(as_text=True)
            if body:
                import json
                try:
                    data = json.loads(body)
                    # Remove sensitive fields
                    sensitive_fields = ['password', 'old_password', 'new_password', 'confirmPassword', 'currentPassword']
                    sanitized_data = {k: ('***REDACTED***' if k in sensitive_fields else v) for k, v in data.items()}
                    logger.info(f"Request body: {json.dumps(sanitized_data)[:500]}")
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, check if it contains password-like data
                    if 'password' not in body.lower():
                        logger.info(f"Request body: {body[:500]}")
                    else:
                        logger.info("Request body: [Contains sensitive data - not logged]")
        except Exception:
            pass

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
