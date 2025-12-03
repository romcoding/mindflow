from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.enhanced_task import EnhancedTask, TaskCategory
from src.models.stakeholder import Stakeholder
from datetime import datetime, timedelta
import json

enhanced_tasks_bp = Blueprint('enhanced_tasks', __name__)

# Task Categories Routes

@enhanced_tasks_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all task categories for the current user"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        categories = TaskCategory.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).order_by(TaskCategory.sort_order, TaskCategory.name).all()
        
        return jsonify({
            'success': True,
            'categories': [category.to_dict() for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create a new task category"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: name'}), 400
        
        # Create new category
        category = TaskCategory(
            user_id=current_user_id,
            name=data['name'],
            description=data.get('description'),
            color=data.get('color', '#3B82F6'),
            icon=data.get('icon'),
            category_type=data.get('category_type', 'project'),
            parent_category_id=data.get('parent_category_id'),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'category': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Enhanced Tasks Routes

@enhanced_tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get tasks with advanced filtering and sorting"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        
        # Get query parameters
        status = request.args.get('status')
        priority = request.args.get('priority')
        category_id = request.args.get('category_id')
        board_column = request.args.get('board_column')
        context = request.args.get('context')
        assigned_stakeholder_id = request.args.get('assigned_stakeholder_id')
        due_soon = request.args.get('due_soon')  # Tasks due in next N days
        overdue = request.args.get('overdue', 'false').lower() == 'true'
        
        # Build query
        query = EnhancedTask.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if board_column:
            query = query.filter_by(board_column=board_column)
        if context:
            query = query.filter_by(context=context)
        if assigned_stakeholder_id:
            query = query.filter_by(assigned_stakeholder_id=assigned_stakeholder_id)
        
        if due_soon:
            try:
                days = int(due_soon)
                due_date_limit = datetime.utcnow() + timedelta(days=days)
                query = query.filter(
                    EnhancedTask.due_date <= due_date_limit,
                    EnhancedTask.status.notin_(['done', 'cancelled'])
                )
            except ValueError:
                pass
        
        if overdue:
            query = query.filter(
                EnhancedTask.due_date < datetime.utcnow(),
                EnhancedTask.status.notin_(['done', 'cancelled'])
            )
        
        # Sort by board position, then by priority and due date
        tasks = query.order_by(
            EnhancedTask.board_column,
            EnhancedTask.board_position,
            EnhancedTask.priority.desc(),
            EnhancedTask.due_date.asc().nullslast()
        ).all()
        
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new enhanced task"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        if 'title' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: title'}), 400
        
        # Verify category exists if provided
        if data.get('category_id'):
            category = TaskCategory.query.filter_by(
                id=data['category_id'],
                user_id=current_user_id
            ).first()
            if not category:
                return jsonify({'success': False, 'error': 'Invalid category ID'}), 400
        
        # Verify stakeholder exists if provided
        if data.get('assigned_stakeholder_id'):
            stakeholder = Stakeholder.query.filter_by(
                id=data['assigned_stakeholder_id'],
                user_id=current_user_id
            ).first()
            if not stakeholder:
                return jsonify({'success': False, 'error': 'Invalid stakeholder ID'}), 400
        
        # Create new task
        task = EnhancedTask(
            user_id=current_user_id,
            title=data['title'],
            description=data.get('description'),
            category_id=data.get('category_id'),
            status=data.get('status', 'todo'),
            priority=data.get('priority', 'medium'),
            energy_level_required=data.get('energy_level_required', 'medium'),
            context=data.get('context'),
            difficulty=data.get('difficulty', 3),
            parent_task_id=data.get('parent_task_id'),
            assigned_stakeholder_id=data.get('assigned_stakeholder_id'),
            estimated_duration=data.get('estimated_duration'),
            is_recurring=data.get('is_recurring', False),
            recurrence_pattern=data.get('recurrence_pattern'),
            board_column=data.get('board_column', 'todo'),
            source=data.get('source', 'manual')
        )
        
        # Handle date fields
        if data.get('due_date'):
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid due_date format'}), 400
        
        if data.get('start_date'):
            try:
                task.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format'}), 400
        
        if data.get('recurrence_end_date'):
            try:
                task.recurrence_end_date = datetime.fromisoformat(data['recurrence_end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid recurrence_end_date format'}), 400
        
        # Handle tags and related stakeholders
        if 'tags' in data:
            task.set_tags_list(data['tags'])
        
        if 'related_stakeholders' in data:
            task.set_related_stakeholders_list(data['related_stakeholders'])
        
        if 'depends_on_tasks' in data:
            task.set_depends_on_list(data['depends_on_tasks'])
        
        # Set board position (add to end of column)
        max_position = db.session.query(db.func.max(EnhancedTask.board_position)).filter_by(
            user_id=current_user_id,
            board_column=task.board_column
        ).scalar() or 0
        task.board_position = max_position + 1
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update an enhanced task"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = EnhancedTask.query.filter_by(
            id=task_id,
            user_id=current_user_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Update basic fields
        updatable_fields = [
            'title', 'description', 'status', 'priority', 'energy_level_required',
            'context', 'difficulty', 'estimated_duration', 'actual_duration',
            'progress_percentage', 'completion_notes', 'is_recurring',
            'recurrence_pattern', 'board_column', 'time_spent', 'external_id'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(task, field, data[field])
        
        # Handle status change to completed
        if data.get('status') == 'done' and task.status != 'done':
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100
        elif data.get('status') != 'done' and task.status == 'done':
            task.completed_at = None
        
        # Handle date fields
        date_fields = ['due_date', 'start_date', 'recurrence_end_date', 'last_worked_on']
        for field in date_fields:
            if field in data:
                if data[field]:
                    try:
                        setattr(task, field, datetime.fromisoformat(data[field].replace('Z', '+00:00')))
                    except ValueError:
                        return jsonify({'success': False, 'error': f'Invalid {field} format'}), 400
                else:
                    setattr(task, field, None)
        
        # Handle relationships
        if 'category_id' in data:
            if data['category_id']:
                category = TaskCategory.query.filter_by(
                    id=data['category_id'],
                    user_id=current_user_id
                ).first()
                if not category:
                    return jsonify({'success': False, 'error': 'Invalid category ID'}), 400
            task.category_id = data['category_id']
        
        if 'assigned_stakeholder_id' in data:
            if data['assigned_stakeholder_id']:
                stakeholder = Stakeholder.query.filter_by(
                    id=data['assigned_stakeholder_id'],
                    user_id=current_user_id
                ).first()
                if not stakeholder:
                    return jsonify({'success': False, 'error': 'Invalid stakeholder ID'}), 400
            task.assigned_stakeholder_id = data['assigned_stakeholder_id']
        
        # Handle lists
        if 'tags' in data:
            task.set_tags_list(data['tags'])
        
        if 'related_stakeholders' in data:
            task.set_related_stakeholders_list(data['related_stakeholders'])
        
        if 'depends_on_tasks' in data:
            task.set_depends_on_list(data['depends_on_tasks'])
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """Move task to different column or position (for Kanban board)"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = EnhancedTask.query.filter_by(
            id=task_id,
            user_id=current_user_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        data = request.get_json()
        new_column = data.get('board_column')
        new_position = data.get('board_position')
        
        if not new_column:
            return jsonify({'success': False, 'error': 'Missing board_column'}), 400
        
        old_column = task.board_column
        old_position = task.board_position
        
        # If moving to a different column
        if new_column != old_column:
            # Update positions in old column (shift up)
            EnhancedTask.query.filter(
                EnhancedTask.user_id == current_user_id,
                EnhancedTask.board_column == old_column,
                EnhancedTask.board_position > old_position
            ).update({
                EnhancedTask.board_position: EnhancedTask.board_position - 1
            })
            
            # Get max position in new column
            max_position = db.session.query(db.func.max(EnhancedTask.board_position)).filter_by(
                user_id=current_user_id,
                board_column=new_column
            ).scalar() or 0
            
            # Set new position
            task.board_column = new_column
            task.board_position = new_position if new_position is not None else max_position + 1
            
            # Update status based on column
            column_status_mapping = {
                'todo': 'todo',
                'in_progress': 'in_progress',
                'review': 'waiting',
                'done': 'done'
            }
            if new_column in column_status_mapping:
                task.status = column_status_mapping[new_column]
                if new_column == 'done':
                    task.completed_at = datetime.utcnow()
                    task.progress_percentage = 100
        
        # If moving within the same column
        elif new_position is not None and new_position != old_position:
            if new_position > old_position:
                # Moving down: shift tasks up
                EnhancedTask.query.filter(
                    EnhancedTask.user_id == current_user_id,
                    EnhancedTask.board_column == old_column,
                    EnhancedTask.board_position > old_position,
                    EnhancedTask.board_position <= new_position
                ).update({
                    EnhancedTask.board_position: EnhancedTask.board_position - 1
                })
            else:
                # Moving up: shift tasks down
                EnhancedTask.query.filter(
                    EnhancedTask.user_id == current_user_id,
                    EnhancedTask.board_column == old_column,
                    EnhancedTask.board_position >= new_position,
                    EnhancedTask.board_position < old_position
                ).update({
                    EnhancedTask.board_position: EnhancedTask.board_position + 1
                })
            
            task.board_position = new_position
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks/kanban', methods=['GET'])
@jwt_required()
def get_kanban_board():
    """Get tasks organized by Kanban columns"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        
        # Define columns
        columns = ['todo', 'in_progress', 'review', 'done']
        
        # Get tasks for each column
        kanban_data = {}
        for column in columns:
            tasks = EnhancedTask.query.filter_by(
                user_id=current_user_id,
                board_column=column
            ).order_by(EnhancedTask.board_position).all()
            
            kanban_data[column] = [task.to_dict() for task in tasks]
        
        return jsonify({
            'success': True,
            'kanban': kanban_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks/analytics', methods=['GET'])
@jwt_required()
def get_task_analytics():
    """Get task analytics and metrics"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        
        # Basic counts
        total_tasks = EnhancedTask.query.filter_by(user_id=current_user_id).count()
        completed_tasks = EnhancedTask.query.filter_by(
            user_id=current_user_id,
            status='done'
        ).count()
        overdue_tasks = EnhancedTask.query.filter(
            EnhancedTask.user_id == current_user_id,
            EnhancedTask.due_date < datetime.utcnow(),
            EnhancedTask.status.notin_(['done', 'cancelled'])
        ).count()
        
        # Priority distribution
        priority_counts = db.session.query(
            EnhancedTask.priority,
            db.func.count(EnhancedTask.id)
        ).filter_by(user_id=current_user_id).group_by(EnhancedTask.priority).all()
        
        priority_distribution = {priority: count for priority, count in priority_counts}
        
        # Status distribution
        status_counts = db.session.query(
            EnhancedTask.status,
            db.func.count(EnhancedTask.id)
        ).filter_by(user_id=current_user_id).group_by(EnhancedTask.status).all()
        
        status_distribution = {status: count for status, count in status_counts}
        
        # Completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Average completion time
        completed_with_duration = EnhancedTask.query.filter(
            EnhancedTask.user_id == current_user_id,
            EnhancedTask.status == 'done',
            EnhancedTask.actual_duration.isnot(None)
        ).all()
        
        avg_completion_time = 0
        if completed_with_duration:
            total_duration = sum(task.actual_duration for task in completed_with_duration)
            avg_completion_time = total_duration / len(completed_with_duration)
        
        # Tasks due this week
        week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        due_this_week = EnhancedTask.query.filter(
            EnhancedTask.user_id == current_user_id,
            EnhancedTask.due_date >= week_start,
            EnhancedTask.due_date <= week_end,
            EnhancedTask.status.notin_(['done', 'cancelled'])
        ).count()
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'due_this_week': due_this_week,
                'completion_rate': round(completion_rate, 2),
                'avg_completion_time_minutes': round(avg_completion_time, 2),
                'priority_distribution': priority_distribution,
                'status_distribution': status_distribution
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@enhanced_tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = EnhancedTask.query.filter_by(
            id=task_id,
            user_id=current_user_id
        ).first()
        
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
        
        # Update positions in the same column
        EnhancedTask.query.filter(
            EnhancedTask.user_id == current_user_id,
            EnhancedTask.board_column == task.board_column,
            EnhancedTask.board_position > task.board_position
        ).update({
            EnhancedTask.board_position: EnhancedTask.board_position - 1
        })
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
