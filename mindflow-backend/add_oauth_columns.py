#!/usr/bin/env python3
"""
Migration script to add OAuth columns to user table
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.models.db import db
from sqlalchemy import text

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        if 'sslmode=' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=prefer"
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    return app

def add_oauth_columns():
    """Add OAuth columns to user table if they don't exist"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting OAuth columns migration...")
        
        try:
            # Check which columns exist
            inspector = db.inspect(db.engine)
            if 'user' not in inspector.get_table_names():
                print("❌ User table does not exist. Run db.create_all() first.")
                return False
            
            columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"📋 Current user table columns: {columns}")
            
            # Add missing columns
            with db.engine.connect() as conn:
                # Add oauth_provider column
                if 'oauth_provider' not in columns:
                    print("➕ Adding oauth_provider column...")
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN oauth_provider VARCHAR(20)'))
                    conn.commit()
                    print("✅ oauth_provider column added")
                else:
                    print("ℹ️  oauth_provider column already exists")
                
                # Add oauth_provider_id column
                if 'oauth_provider_id' not in columns:
                    print("➕ Adding oauth_provider_id column...")
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN oauth_provider_id VARCHAR(255)'))
                    conn.commit()
                    print("✅ oauth_provider_id column added")
                else:
                    print("ℹ️  oauth_provider_id column already exists")
                
                # Add avatar_url column
                if 'avatar_url' not in columns:
                    print("➕ Adding avatar_url column...")
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN avatar_url VARCHAR(500)'))
                    conn.commit()
                    print("✅ avatar_url column added")
                else:
                    print("ℹ️  avatar_url column already exists")
                
                # Make password_hash nullable (if it's not already)
                # Check if password_hash is nullable
                conn.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = 'password_hash'
                """))
                result = conn.fetchone()
                if result and result[0] == 'NO':
                    print("➕ Making password_hash nullable...")
                    conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash DROP NOT NULL'))
                    conn.commit()
                    print("✅ password_hash is now nullable")
                else:
                    print("ℹ️  password_hash is already nullable")
            
            # Verify columns were added
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            print(f"📋 Updated user table columns: {columns}")
            
            required_columns = ['oauth_provider', 'oauth_provider_id', 'avatar_url']
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                print(f"❌ Missing columns: {missing}")
                return False
            else:
                print("✅ All OAuth columns added successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = add_oauth_columns()
    sys.exit(0 if success else 1)

