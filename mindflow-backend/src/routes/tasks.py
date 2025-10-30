from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.task import Task
from src.models.stakeholder import Stakeholder
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        current_user_id = 1
        
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
def create_task():
    try:
        current_user_id = 1
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
            stakeholder_id=stakeholder_id
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
def get_task(task_id):
    try:
        current_user_id = 1
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({'task': task.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get task', 'details': str(e)}), 500

@tasks_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        current_user_id = 1
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

@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        current_user_id = 1
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
def toggle_task_completion(task_id):
    try:
        current_user_id = 1
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
