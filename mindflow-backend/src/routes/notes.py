from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.note import Note
from src.models.stakeholder import Stakeholder

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes', methods=['GET'])
@jwt_required()
def get_notes():
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        
        # Get query parameters for filtering
        category = request.args.get('category')
        stakeholder_id = request.args.get('stakeholder_id')
        
        # Build query
        query = Note.query.filter_by(user_id=current_user_id)
        
        if category:
            query = query.filter_by(category=category)
        
        if stakeholder_id:
            try:
                stakeholder_id = int(stakeholder_id)
                query = query.filter_by(stakeholder_id=stakeholder_id)
            except ValueError:
                return jsonify({'error': 'Invalid stakeholder_id'}), 400
        
        # Order by creation date (newest first)
        notes = query.order_by(Note.created_at.desc()).all()
        
        return jsonify({
            'notes': [note.to_dict() for note in notes]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get notes', 'details': str(e)}), 500

@notes_bp.route('/notes', methods=['POST'])
@jwt_required()
def create_note():
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        if not data.get('content'):
            return jsonify({'error': 'Content is required'}), 400
        
        # Validate stakeholder if provided
        stakeholder_id = data.get('stakeholder_id')
        if stakeholder_id:
            stakeholder = Stakeholder.query.filter_by(
                id=stakeholder_id, 
                user_id=current_user_id
            ).first()
            if not stakeholder:
                return jsonify({'error': 'Stakeholder not found'}), 404
        
        # Create note
        note = Note(
            user_id=current_user_id,
            title=data.get('title', '').strip() or None,
            content=data['content'].strip(),
            category=data.get('category', '').strip() or None,
            stakeholder_id=stakeholder_id
        )
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify({
            'message': 'Note created successfully',
            'note': note.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create note', 'details': str(e)}), 500

@notes_bp.route('/notes/<int:note_id>', methods=['GET'])
@jwt_required()
def get_note(note_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        return jsonify({'note': note.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get note', 'details': str(e)}), 500

@notes_bp.route('/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            note.title = data['title'].strip() or None
        
        if 'content' in data:
            if not data['content'].strip():
                return jsonify({'error': 'Content cannot be empty'}), 400
            note.content = data['content'].strip()
        
        if 'category' in data:
            note.category = data['category'].strip() or None
        
        if 'stakeholder_id' in data:
            stakeholder_id = data['stakeholder_id']
            if stakeholder_id:
                stakeholder = Stakeholder.query.filter_by(
                    id=stakeholder_id, 
                    user_id=current_user_id
                ).first()
                if not stakeholder:
                    return jsonify({'error': 'Stakeholder not found'}), 404
            note.stakeholder_id = stakeholder_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Note updated successfully',
            'note': note.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update note', 'details': str(e)}), 500

@notes_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=current_user_id).first()
        
        if not note:
            return jsonify({'error': 'Note not found'}), 404
        
        db.session.delete(note)
        db.session.commit()
        
        return jsonify({'message': 'Note deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete note', 'details': str(e)}), 500
