from flask import Blueprint, jsonify
from src.models.db import db
import os
import psycopg2
from src.models.user import User
# from src.models.organization import Organization  # Temporarily disabled
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from src.models.note import Note
from src.models.enhanced_task import EnhancedTask, TaskCategory
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/reset-db', methods=['POST'])
def reset_database():
    """Reset database schema - USE WITH CAUTION - This will delete all data"""
    try:
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Verify reset
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check if user table has org_id column
        user_columns = []
        if 'user' in tables:
            user_columns = [col['name'] for col in inspector.get_columns('user')]
        
        return jsonify({
            'success': True,
            'message': 'Database reset completed - all data deleted and tables recreated',
            'tables_created': tables,
            'user_columns': user_columns,
            'org_id_removed': 'org_id' not in user_columns
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/drop-org-id', methods=['POST'])
def drop_org_id_column():
    """Drop org_id column from user table using direct SQL"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({
                'success': False,
                'error': 'No DATABASE_URL found'
            }), 500
        
        # Parse the database URL
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Connect and drop the column
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if column exists first
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'org_id'
        """)
        
        column_exists = cursor.fetchone() is not None
        
        if column_exists:
            # Drop the org_id column
            cursor.execute('ALTER TABLE "user" DROP COLUMN IF EXISTS org_id')
            conn.commit()
            message = 'org_id column dropped successfully'
        else:
            message = 'org_id column does not exist'
        
        # Verify current columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': message,
            'column_existed': column_exists,
            'current_columns': columns,
            'org_id_removed': 'org_id' not in columns
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/db-status', methods=['GET'])
def database_status():
    """Check database status"""
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        user_columns = []
        if 'user' in tables:
            user_columns = [col['name'] for col in inspector.get_columns('user')]
        
        return jsonify({
            'success': True,
            'tables': tables,
            'user_columns': user_columns,
            'org_id_exists': 'org_id' in user_columns
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
