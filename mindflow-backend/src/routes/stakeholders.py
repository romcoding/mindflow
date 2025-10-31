from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.stakeholder import Stakeholder
from datetime import datetime

stakeholders_bp = Blueprint('stakeholders', __name__)

@stakeholders_bp.route('/stakeholders', methods=['GET'])
@jwt_required()
def get_stakeholders():
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters for filtering
        sentiment = request.args.get('sentiment')
        company = request.args.get('company')
        
        # Build query
        query = Stakeholder.query.filter_by(user_id=current_user_id)
        
        if sentiment:
            query = query.filter_by(sentiment=sentiment)
        
        if company:
            query = query.filter(Stakeholder.company.ilike(f'%{company}%'))
        
        # Order by name
        stakeholders = query.order_by(Stakeholder.name).all()
        
        return jsonify({
            'stakeholders': [stakeholder.to_dict() for stakeholder in stakeholders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stakeholders', 'details': str(e)}), 500

@stakeholders_bp.route('/stakeholders', methods=['POST'])
@jwt_required()
def create_stakeholder():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        # Validate sentiment
        valid_sentiments = ['positive', 'neutral', 'negative']
        sentiment = data.get('sentiment', 'neutral')
        if sentiment not in valid_sentiments:
            return jsonify({'error': 'Sentiment must be positive, neutral, or negative'}), 400
        
        # Validate influence and interest
        influence = data.get('influence', 5)
        interest = data.get('interest', 5)
        
        try:
            influence = int(influence)
            interest = int(interest)
            if not (1 <= influence <= 10) or not (1 <= interest <= 10):
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({'error': 'Influence and interest must be integers between 1 and 10'}), 400
        
        # Create stakeholder
        stakeholder = Stakeholder(
            user_id=current_user_id,
            name=data['name'].strip(),
            role=data.get('role', '').strip() or None,
            company=data.get('company', '').strip() or None,
            department=data.get('department', '').strip() or None,
            work_style=data.get('work_style', '').strip() or None,
            email=data.get('email', '').strip() or None,
            phone=data.get('phone', '').strip() or None,
            birthday=data.get('birthday', '').strip() or None,
            personal_notes=data.get('personal_notes', '').strip() or None,
            sentiment=sentiment,
            influence=influence,
            interest=interest
        )
        
        # Handle tags
        tags = data.get('tags', [])
        if isinstance(tags, list):
            stakeholder.set_tags_list(tags)
        
        db.session.add(stakeholder)
        db.session.commit()
        
        return jsonify({
            'message': 'Stakeholder created successfully',
            'stakeholder': stakeholder.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create stakeholder', 'details': str(e)}), 500

@stakeholders_bp.route('/stakeholders/<int:stakeholder_id>', methods=['GET'])
@jwt_required()
def get_stakeholder(stakeholder_id):
    try:
        current_user_id = get_jwt_identity()
        stakeholder = Stakeholder.query.filter_by(
            id=stakeholder_id, 
            user_id=current_user_id
        ).first()
        
        if not stakeholder:
            return jsonify({'error': 'Stakeholder not found'}), 404
        
        return jsonify({'stakeholder': stakeholder.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get stakeholder', 'details': str(e)}), 500

@stakeholders_bp.route('/stakeholders/<int:stakeholder_id>', methods=['PUT'])
@jwt_required()
def update_stakeholder(stakeholder_id):
    try:
        current_user_id = get_jwt_identity()
        stakeholder = Stakeholder.query.filter_by(
            id=stakeholder_id, 
            user_id=current_user_id
        ).first()
        
        if not stakeholder:
            return jsonify({'error': 'Stakeholder not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            if not data['name'].strip():
                return jsonify({'error': 'Name cannot be empty'}), 400
            stakeholder.name = data['name'].strip()
        
        if 'role' in data:
            stakeholder.role = data['role'].strip() or None
        
        if 'company' in data:
            stakeholder.company = data['company'].strip() or None
        
        if 'department' in data:
            stakeholder.department = data['department'].strip() or None
        
        if 'work_style' in data:
            stakeholder.work_style = data['work_style'].strip() or None
        
        if 'email' in data:
            stakeholder.email = data['email'].strip() or None
        
        if 'phone' in data:
            stakeholder.phone = data['phone'].strip() or None
        
        if 'birthday' in data:
            stakeholder.birthday = data['birthday'].strip() or None
        
        if 'personal_notes' in data:
            stakeholder.personal_notes = data['personal_notes'].strip() or None
        
        if 'sentiment' in data:
            valid_sentiments = ['positive', 'neutral', 'negative']
            if data['sentiment'] not in valid_sentiments:
                return jsonify({'error': 'Sentiment must be positive, neutral, or negative'}), 400
            stakeholder.sentiment = data['sentiment']
        
        if 'influence' in data:
            try:
                influence = int(data['influence'])
                if not (1 <= influence <= 10):
                    raise ValueError()
                stakeholder.influence = influence
            except (ValueError, TypeError):
                return jsonify({'error': 'Influence must be an integer between 1 and 10'}), 400
        
        if 'interest' in data:
            try:
                interest = int(data['interest'])
                if not (1 <= interest <= 10):
                    raise ValueError()
                stakeholder.interest = interest
            except (ValueError, TypeError):
                return jsonify({'error': 'Interest must be an integer between 1 and 10'}), 400
        
        if 'tags' in data:
            tags = data['tags']
            if isinstance(tags, list):
                stakeholder.set_tags_list(tags)
        
        # Update last contact if this is a contact update
        if any(field in data for field in ['email', 'phone']):
            stakeholder.last_contact = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Stakeholder updated successfully',
            'stakeholder': stakeholder.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update stakeholder', 'details': str(e)}), 500

@stakeholders_bp.route('/stakeholders/<int:stakeholder_id>', methods=['DELETE'])
@jwt_required()
def delete_stakeholder(stakeholder_id):
    try:
        current_user_id = get_jwt_identity()
        stakeholder = Stakeholder.query.filter_by(
            id=stakeholder_id, 
            user_id=current_user_id
        ).first()
        
        if not stakeholder:
            return jsonify({'error': 'Stakeholder not found'}), 404
        
        db.session.delete(stakeholder)
        db.session.commit()
        
        return jsonify({'message': 'Stakeholder deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete stakeholder', 'details': str(e)}), 500

@stakeholders_bp.route('/stakeholders/<int:stakeholder_id>/contact', methods=['PATCH'])
@jwt_required()
def update_last_contact(stakeholder_id):
    try:
        current_user_id = get_jwt_identity()
        stakeholder = Stakeholder.query.filter_by(
            id=stakeholder_id, 
            user_id=current_user_id
        ).first()
        
        if not stakeholder:
            return jsonify({'error': 'Stakeholder not found'}), 404
        
        stakeholder.last_contact = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Last contact updated successfully',
            'stakeholder': stakeholder.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update last contact', 'details': str(e)}), 500
