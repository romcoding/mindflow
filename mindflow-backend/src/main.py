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
from src.routes.ai_parser import ai_parser_bp
from src.routes.linkedin import linkedin_bp
from src.routes.ai_assistant import ai_assistant_bp
from src.routes.telegram_bot import telegram_bp
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
# JWT_SECRET_KEY - CRITICAL: Must match between token creation and validation
# If JWT_SECRET_KEY is not set, use SECRET_KEY to ensure consistency
jwt_secret = os.environ.get('JWT_SECRET_KEY')
if not jwt_secret:
    # Fallback to SECRET_KEY to ensure tokens created with one secret can be validated with the same
    jwt_secret = os.environ.get('SECRET_KEY', 'jwt-secret-change-in-production')
    logger.warning("JWT_SECRET_KEY not set, using SECRET_KEY as fallback. This is OK if SECRET_KEY is stable.")
else:
    logger.info("JWT_SECRET_KEY is set from environment")
    # Strip whitespace in case there's any
    jwt_secret = jwt_secret.strip()

app.config['JWT_SECRET_KEY'] = jwt_secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_ALGORITHM'] = 'HS256'  # Explicitly set algorithm
app.config['JWT_IDENTITY_CLAIM'] = 'sub'  # Use 'sub' claim for identity

# Log JWT configuration (without exposing the actual secret)
logger.info(f"JWT configured: algorithm=HS256, secret_key_set={bool(jwt_secret)}, secret_key_length={len(jwt_secret)}, expires={app.config['JWT_ACCESS_TOKEN_EXPIRES']}")
# Session configuration for OAuth state management
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allows OAuth redirects

# Initialize extensions
# IMPORTANT: JWTManager must be initialized AFTER setting JWT_SECRET_KEY
jwt = JWTManager(app)
bcrypt.init_app(app)

# Verify JWT configuration after initialization
logger.info(f"JWTManager initialized with secret key length: {len(app.config.get('JWT_SECRET_KEY', ''))}")

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired', 'message': 'Please log in again'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"❌ Invalid token error: {str(error)}")
    logger.error(f"JWT_SECRET_KEY configured: {bool(app.config.get('JWT_SECRET_KEY'))}")
    logger.error(f"JWT_SECRET_KEY length: {len(app.config.get('JWT_SECRET_KEY', ''))}")
    logger.error(f"JWT_ALGORITHM: {app.config.get('JWT_ALGORITHM', 'NOT SET')}")
    logger.error(f"Authorization header: {request.headers.get('Authorization', 'NOT PRESENT')[:50] if request.headers.get('Authorization') else 'NOT PRESENT'}")
    return jsonify({'error': 'Invalid token', 'message': 'Please log in again'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization required', 'message': 'Please provide a valid token'}), 401

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
app.register_blueprint(ai_parser_bp, url_prefix='/api')
app.register_blueprint(linkedin_bp, url_prefix='/api')
app.register_blueprint(ai_assistant_bp, url_prefix='/api')
app.register_blueprint(telegram_bp, url_prefix='/api')

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
    'pool_pre_ping': True,  # Verify connections before using (reconnects if connection is dead)
    'pool_recycle': int(os.environ.get('SQLALCHEMY_POOL_RECYCLE_SECONDS', 300)),  # Recycle connections after 5 minutes
    'pool_size': int(os.environ.get('SQLALCHEMY_POOL_SIZE', 2)),  # Reduced for free tier (Render free tier has limits)
    'max_overflow': int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 5)),  # Reduced for free tier
    'pool_timeout': 30,  # Timeout for getting connection from pool
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
        # Try to add OAuth columns if they don't exist (for existing databases)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'user' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('user')]
                required_oauth_columns = ['oauth_provider', 'oauth_provider_id', 'avatar_url']
                missing_columns = [col for col in required_oauth_columns if col not in columns]
                
                if missing_columns:
                    logger.info(f"Adding missing OAuth columns: {missing_columns}")
                    with db.engine.connect() as conn:
                        # PostgreSQL doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN
                        # So we check first and only add if missing
                        if 'oauth_provider' not in columns:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN oauth_provider VARCHAR(20)'))
                        if 'oauth_provider_id' not in columns:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN oauth_provider_id VARCHAR(255)'))
                        if 'avatar_url' not in columns:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN avatar_url VARCHAR(500)'))
                        # Make password_hash nullable if needed (PostgreSQL specific)
                        conn.execute(text("""
                            DO $$ 
                            BEGIN
                                IF EXISTS (
                                    SELECT 1 FROM information_schema.columns 
                                    WHERE table_name = 'user' 
                                    AND column_name = 'password_hash' 
                                    AND is_nullable = 'NO'
                                ) THEN
                                    ALTER TABLE "user" ALTER COLUMN password_hash DROP NOT NULL;
                                END IF;
                            END $$;
                        """))
                        conn.commit()
                    logger.info("OAuth columns added successfully")
        except Exception as migration_error:
            logger.warning(f"Could not add OAuth columns automatically: {str(migration_error)[:200]}")
            logger.info("You may need to run add_oauth_columns.py manually")
        
        # Try to add missing task columns if they don't exist
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'task' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('task')]
                required_task_columns = ['board_column', 'board_position', 'status']
                missing_task_columns = [col for col in required_task_columns if col not in columns]
                
                if missing_task_columns:
                    logger.info(f"Adding missing Task columns: {missing_task_columns}")
                    with db.engine.connect() as conn:
                        if 'board_column' not in columns:
                            conn.execute(text('ALTER TABLE task ADD COLUMN board_column VARCHAR(50) DEFAULT \'todo\''))
                        if 'board_position' not in columns:
                            conn.execute(text('ALTER TABLE task ADD COLUMN board_position INTEGER DEFAULT 0'))
                        if 'status' not in columns:
                            conn.execute(text('ALTER TABLE task ADD COLUMN status VARCHAR(50) DEFAULT \'todo\''))
                        conn.commit()
                    logger.info("Task columns added successfully")
        except Exception as migration_error:
            logger.warning(f"Could not add Task columns automatically: {str(migration_error)[:200]}")
        
        # Try to add missing stakeholder columns if they don't exist
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'stakeholder' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('stakeholder')]
                # All columns from the Stakeholder model that might be missing
                required_stakeholder_columns = [
                    'family_info', 'hobbies', 'education', 'career_history',
                    'job_title', 'seniority_level', 'years_experience', 'specializations',
                    'decision_making_authority', 'budget_authority', 'location', 'timezone',
                    'preferred_language', 'cultural_background', 'preferred_communication_method',
                    'communication_frequency', 'best_contact_time', 'communication_style',
                    'linkedin_url', 'twitter_handle', 'other_social_links', 'current_projects',
                    'availability_status', 'trust_level', 'collaboration_history',
                    'conflict_resolution_style', 'strategic_value', 'risk_level',
                    'opportunity_potential', 'sentiment', 'influence', 'interest', 'tags',
                    'created_at', 'updated_at', 'last_contact'
                ]
                missing_columns = [col for col in required_stakeholder_columns if col not in columns]
                
                if missing_columns:
                    logger.info(f"Adding missing stakeholder columns: {missing_columns}")
                    with db.engine.connect() as conn:
                        # Add each missing column with appropriate type
                        if 'family_info' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN family_info TEXT'))
                        if 'hobbies' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN hobbies TEXT'))
                        if 'education' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN education TEXT'))
                        if 'career_history' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN career_history TEXT'))
                        if 'job_title' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN job_title VARCHAR(100)'))
                        if 'seniority_level' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN seniority_level VARCHAR(50)'))
                        if 'years_experience' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN years_experience INTEGER'))
                        if 'specializations' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN specializations TEXT'))
                        if 'decision_making_authority' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN decision_making_authority VARCHAR(50) DEFAULT 'low'"))
                        if 'budget_authority' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN budget_authority VARCHAR(50) DEFAULT 'none'"))
                        if 'location' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN location VARCHAR(100)'))
                        if 'timezone' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN timezone VARCHAR(50)'))
                        if 'preferred_language' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN preferred_language VARCHAR(50) DEFAULT 'English'"))
                        if 'cultural_background' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN cultural_background VARCHAR(100)'))
                        if 'preferred_communication_method' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN preferred_communication_method VARCHAR(50) DEFAULT 'email'"))
                        if 'communication_frequency' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN communication_frequency VARCHAR(50) DEFAULT 'weekly'"))
                        if 'best_contact_time' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN best_contact_time VARCHAR(100)'))
                        if 'communication_style' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN communication_style VARCHAR(50)'))
                        if 'linkedin_url' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN linkedin_url VARCHAR(200)'))
                        if 'twitter_handle' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN twitter_handle VARCHAR(50)'))
                        if 'other_social_links' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN other_social_links TEXT'))
                        if 'current_projects' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN current_projects TEXT'))
                        if 'availability_status' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN availability_status VARCHAR(50) DEFAULT 'available'"))
                        if 'trust_level' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN trust_level INTEGER DEFAULT 5'))
                        if 'collaboration_history' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN collaboration_history TEXT'))
                        if 'conflict_resolution_style' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN conflict_resolution_style VARCHAR(50)'))
                        if 'strategic_value' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN strategic_value VARCHAR(50) DEFAULT 'medium'"))
                        if 'risk_level' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN risk_level VARCHAR(50) DEFAULT 'low'"))
                        if 'opportunity_potential' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN opportunity_potential VARCHAR(50) DEFAULT 'medium'"))
                        if 'sentiment' not in columns:
                            conn.execute(text("ALTER TABLE stakeholder ADD COLUMN sentiment VARCHAR(20) DEFAULT 'neutral'"))
                        if 'influence' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN influence INTEGER DEFAULT 5'))
                        if 'interest' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN interest INTEGER DEFAULT 5'))
                        if 'tags' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN tags TEXT'))
                        if 'created_at' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                        if 'updated_at' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
                        if 'last_contact' not in columns:
                            conn.execute(text('ALTER TABLE stakeholder ADD COLUMN last_contact TIMESTAMP'))
                        conn.commit()
                    logger.info(f"Stakeholder columns added successfully: {len(missing_columns)} columns")
        except Exception as migration_error:
            logger.warning(f"Could not add stakeholder columns automatically: {str(migration_error)[:200]}")
        
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

# JWT configuration debug endpoint (for troubleshooting)
@app.route('/api/debug/jwt-config', methods=['GET'])
def debug_jwt_config():
    """Debug endpoint to verify JWT configuration"""
    config_info = {
        'jwt_secret_key_set': bool(app.config.get('JWT_SECRET_KEY')),
        'jwt_secret_key_length': len(app.config.get('JWT_SECRET_KEY', '')),
        'jwt_algorithm': app.config.get('JWT_ALGORITHM', 'NOT SET'),
        'jwt_access_token_expires': str(app.config.get('JWT_ACCESS_TOKEN_EXPIRES')),
        'jwt_token_location': app.config.get('JWT_TOKEN_LOCATION', []),
        'secret_key_set': bool(app.config.get('SECRET_KEY')),
        'secret_key_length': len(app.config.get('SECRET_KEY', '')),
        'env_jwt_secret_key_set': bool(os.environ.get('JWT_SECRET_KEY')),
        'env_secret_key_set': bool(os.environ.get('SECRET_KEY')),
        'secret_keys_match': app.config.get('JWT_SECRET_KEY') == app.config.get('SECRET_KEY'),
        'env_secret_keys_match': os.environ.get('JWT_SECRET_KEY') == os.environ.get('SECRET_KEY'),
    }
    return jsonify(config_info), 200

# Test token validation endpoint
@app.route('/api/debug/test-token', methods=['POST'])
def test_token_validation():
    """Test endpoint to manually validate a token"""
    try:
        from flask_jwt_extended import decode_token
        from flask import request as req
        
        data = req.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 400
        
        # Try to decode the token
        try:
            decoded = decode_token(token)
            return jsonify({
                'success': True,
                'decoded': {
                    'sub': decoded.get('sub'),
                    'exp': decoded.get('exp'),
                    'iat': decoded.get('iat'),
                    'type': decoded.get('type'),
                },
                'jwt_secret_key_length': len(app.config.get('JWT_SECRET_KEY', '')),
            }), 200
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'jwt_secret_key_length': len(app.config.get('JWT_SECRET_KEY', '')),
            }), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    
    # Log Authorization header presence (not the actual token)
    auth_header = request.headers.get('Authorization', '')
    has_auth = bool(auth_header)
    auth_preview = auth_header[:20] + '...' if auth_header and len(auth_header) > 20 else 'None'
    
    logger.info(f"[{request.method}] {request.path} - Origin: {request.headers.get('Origin', 'N/A')} - IP: {request.remote_addr} - Auth: {has_auth} ({auth_preview})")
    
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
