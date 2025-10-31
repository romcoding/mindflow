#!/usr/bin/env python3
"""
Database migration script to fix schema issues
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.db import db
from src.models.user import User
from src.models.organization import Organization
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.enhanced_task import EnhancedTask, TaskCategory
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction
from flask import Flask

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

def migrate_database():
    """Run database migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting database migration...")
        
        try:
            # Drop all tables and recreate them with the correct schema
            print("Dropping all existing tables...")
            db.drop_all()
            
            print("Creating all tables with updated schema...")
            db.create_all()
            
            print("Database migration completed successfully!")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            # Check if user table has org_id column
            if 'user' in tables:
                columns = [col['name'] for col in inspector.get_columns('user')]
                print(f"User table columns: {columns}")
                
                if 'org_id' in columns:
                    print("✅ org_id column successfully added to user table")
                else:
                    print("❌ org_id column still missing from user table")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
