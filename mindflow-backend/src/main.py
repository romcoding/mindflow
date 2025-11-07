import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from src.models.db import db, bcrypt
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

# Initialize extensions
jwt = JWTManager(app)
bcrypt.init_app(app)

# Rate Limiting setup (no app context at import time)
if os.environ.get('REDIS_URL'):
    limiter.storage_uri = os.environ['REDIS_URL']
else:
    limiter.storage_uri = 'memory://'
limiter.init_app(app)

# CORS configuration - allow all origins in production (adjust as needed)
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
CORS(app, 
     origins=allowed_origins if allowed_origins != '*' else ['*'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])

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
    app.config["SQLALCHEMY_DATABASE_URI"] = f"{database_url}?sslmode=require"
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Import all models to ensure they're registered
from src.models.user import User
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction
from src.models.enhanced_task import EnhancedTask

with app.app_context():
    db.create_all()

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
