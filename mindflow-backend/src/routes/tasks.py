from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from datetime import datetime, timedelta

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        # Log token validation success
        import logging
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id_str = get_jwt_identity()
        current_user_id = int(current_user_id_str) if current_user_id_str else None
        logging.info(f"✅ Token validated successfully for user {current_user_id}")
        
        # Auto-cleanup: delete tasks in "done" column for more than 1 day
        try:
            cutoff = datetime.utcnow() - timedelta(days=1)
            stale_done_tasks = Task.query.filter(
                Task.user_id == current_user_id,
                Task.board_column == 'done',
                Task.updated_at < cutoff
            ).all()
            if stale_done_tasks:
                for t in stale_done_tasks:
                    db.session.delete(t)
                db.session.commit()
                logging.info(f"Auto-cleaned {len(stale_done_tasks)} done task(s) for user {current_user_id}")
        except Exception as cleanup_err:
            logging.warning(f"Done task cleanup failed: {cleanup_err}")
            db.session.rollback()
        
        # Get query parameters for filtering
        completed = request.args.get('completed')
        priority = request.args.get('priority')
        due_date = request.args.get('due_date')
        
        # Build query
        query = Task.query.filter_by(user_id=current_user_id)
        
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            query = query.filter_by(completed=completed_bool)
        
        if priority:
            query = query.filter_by(priority=priority)
        
        if due_date:
            query = query.filter_by(due_date=due_date)
        
        # Order by priority and creation date
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        tasks = query.all()
        tasks.sort(key=lambda x: (priority_order.get(x.priority, 4), x.created_at))
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get tasks', 'details': str(e)}), 500

@tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Validate priority
        valid_priorities = ['low', 'medium', 'high']
        priority = data.get('priority', 'medium')
        if priority not in valid_priorities:
            return jsonify({'error': 'Priority must be low, medium, or high'}), 400
        
        # Validate stakeholder if provided
        stakeholder_id = data.get('stakeholder_id')
        if stakeholder_id:
            stakeholder = Stakeholder.query.filter_by(
                id=stakeholder_id, 
                user_id=current_user_id
            ).first()
            if not stakeholder:
                return jsonify({'error': 'Stakeholder not found'}), 404
        
        # Create task
        task = Task(
            user_id=current_user_id,
            title=data['title'].strip(),
            description=data.get('description', '').strip() or None,
            due_date=data.get('due_date'),
            priority=priority,
            stakeholder_id=stakeholder_id,
            board_column=data.get('board_column', 'todo'),
            board_position=data.get('board_position', 0),
            status=data.get('status', 'todo')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({'task': task.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            if not data['title'].strip():
                return jsonify({'error': 'Title cannot be empty'}), 400
            task.title = data['title'].strip()
        
        if 'description' in data:
            task.description = data['description'].strip() or None
        
        if 'due_date' in data:
            task.due_date = data['due_date']
        
        if 'priority' in data:
            valid_priorities = ['low', 'medium', 'high']
            if data['priority'] not in valid_priorities:
                return jsonify({'error': 'Priority must be low, medium, or high'}), 400
            task.priority = data['priority']
        
        if 'completed' in data:
            task.completed = bool(data['completed'])
        
        if 'stakeholder_id' in data:
            stakeholder_id = data['stakeholder_id']
            if stakeholder_id:
                stakeholder = Stakeholder.query.filter_by(
                    id=stakeholder_id, 
                    user_id=current_user_id
                ).first()
                if not stakeholder:
                    return jsonify({'error': 'Stakeholder not found'}), 404
            task.stakeholder_id = stakeholder_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>/move', methods=['POST'])
@jwt_required()
def move_task(task_id):
    """Move task to different column or position (for Kanban board)"""
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(
            id=task_id,
            user_id=current_user_id
        ).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.get_json()
        new_column = data.get('board_column')
        new_position = data.get('board_position')
        
        if not new_column:
            return jsonify({'error': 'Missing board_column'}), 400
        
        # Ensure task has board_column set (for tasks created before board_column was added)
        if not hasattr(task, 'board_column') or not task.board_column:
            task.board_column = 'todo'
        if not hasattr(task, 'board_position') or task.board_position is None:
            task.board_position = 0
        
        old_column = task.board_column
        old_position = task.board_position
        
        # If moving to a different column
        if new_column != old_column:
            # Update positions in old column (shift up)
            Task.query.filter(
                Task.user_id == current_user_id,
                Task.board_column == old_column,
                Task.board_position > old_position
            ).update({
                Task.board_position: Task.board_position - 1
            }, synchronize_session=False)
            
            # Get max position in new column
            from sqlalchemy import func
            max_position = db.session.query(func.max(Task.board_position)).filter_by(
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
                if hasattr(task, 'status'):
                    task.status = column_status_mapping[new_column]
                if new_column == 'done':
                    task.completed = True
                elif old_column == 'done':
                    task.completed = False
        
        # If moving within the same column
        elif new_position is not None and new_position != old_position:
            if new_position > old_position:
                # Moving down: shift tasks up
                Task.query.filter(
                    Task.user_id == current_user_id,
                    Task.board_column == old_column,
                    Task.board_position > old_position,
                    Task.board_position <= new_position
                ).update({
                    Task.board_position: Task.board_position - 1
                }, synchronize_session=False)
            else:
                # Moving up: shift tasks down
                Task.query.filter(
                    Task.user_id == current_user_id,
                    Task.board_column == old_column,
                    Task.board_position >= new_position,
                    Task.board_position < old_position
                ).update({
                    Task.board_position: Task.board_position + 1
                }, synchronize_session=False)
            
            task.board_position = new_position
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Task moved successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to move task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Task deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_task_completion(task_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        task.completed = not task.completed
        db.session.commit()
        
        return jsonify({
            'message': f'Task marked as {"completed" if task.completed else "incomplete"}',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle task completion', 'details': str(e)}), 500
