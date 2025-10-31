#!/usr/bin/env python3
"""
Simple database reset script - USE WITH CAUTION
This will drop and recreate all tables
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from src.models.db import db
from src.models.user import User
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.enhanced_task import EnhancedTask, TaskCategory
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///mindflow.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def reset_database():
    """Reset database - drop and recreate all tables"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database reset...")
        
        try:
            print("🗑️  Dropping all existing tables...")
            db.drop_all()
            
            print("🏗️  Creating all tables with clean schema...")
            db.create_all()
            
            print("✅ Database reset completed successfully!")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {tables}")
            
            # Check user table structure
            if 'user' in tables:
                columns = [col['name'] for col in inspector.get_columns('user')]
                print(f"👤 User table columns: {columns}")
                
                if 'org_id' not in columns:
                    print("✅ org_id column successfully removed from user table")
                else:
                    print("❌ org_id column still exists in user table")
            
            return True
            
        except Exception as e:
            print(f"❌ Database reset failed: {e}")
            return False

if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)
