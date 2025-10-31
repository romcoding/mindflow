from flask import Blueprint, jsonify
from src.models.db import db
from src.models.user import User
from src.models.organization import Organization
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
