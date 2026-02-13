from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.stakeholder import Stakeholder
from datetime import datetime

stakeholders_bp = Blueprint('stakeholders', __name__)

def clean_optional(value):
    """
    Safely strip a value that may be None or non-string.
    Returns None if the resulting string is empty.
    """
    if value is None:
        return None
    try:
        value_str = str(value).strip()
    except Exception:
        return None
    return value_str or None

@stakeholders_bp.route('/stakeholders', methods=['GET'])
@jwt_required()
def get_stakeholders():
    try:
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
        
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
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
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
        
        # Helper for safe int conversion
        def safe_int(val, default=None):
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        # Validate trust_level
        trust_level = safe_int(data.get('trust_level'), 5)
        if not (1 <= trust_level <= 10):
            trust_level = 5

        # Create stakeholder with all model fields
        stakeholder = Stakeholder(
            user_id=current_user_id,
            name=clean_optional(data.get('name')),
            role=clean_optional(data.get('role')),
            company=clean_optional(data.get('company')),
            department=clean_optional(data.get('department')),
            work_style=clean_optional(data.get('work_style')),
            email=clean_optional(data.get('email')),
            phone=clean_optional(data.get('phone')),
            birthday=clean_optional(data.get('birthday')),
            personal_notes=clean_optional(data.get('personal_notes')),
            sentiment=sentiment,
            influence=influence,
            interest=interest,
            # Professional details
            job_title=clean_optional(data.get('job_title')),
            seniority_level=clean_optional(data.get('seniority_level')),
            years_experience=safe_int(data.get('years_experience')),
            specializations=clean_optional(data.get('specializations')) if isinstance(data.get('specializations'), str) else None,
            decision_making_authority=clean_optional(data.get('decision_making_authority')),
            budget_authority=clean_optional(data.get('budget_authority')),
            # Personal
            family_info=clean_optional(data.get('family_info')),
            hobbies=clean_optional(data.get('hobbies')),
            education=clean_optional(data.get('education')),
            career_history=clean_optional(data.get('career_history')),
            # Geographic
            location=clean_optional(data.get('location')),
            timezone=clean_optional(data.get('timezone')),
            preferred_language=clean_optional(data.get('preferred_language')),
            cultural_background=clean_optional(data.get('cultural_background')),
            # Communication
            preferred_communication_method=clean_optional(data.get('preferred_communication_method')),
            communication_frequency=clean_optional(data.get('communication_frequency')),
            best_contact_time=clean_optional(data.get('best_contact_time')),
            communication_style=clean_optional(data.get('communication_style')),
            # Social
            linkedin_url=clean_optional(data.get('linkedin_url')),
            twitter_handle=clean_optional(data.get('twitter_handle')),
            # Relationship
            trust_level=trust_level,
            strategic_value=clean_optional(data.get('strategic_value')),
            availability_status=clean_optional(data.get('availability_status')),
        )
        
        # Handle tags
        tags = data.get('tags', [])
        if isinstance(tags, list):
            stakeholder.set_tags_list(tags)

        # Handle specializations as list
        specializations = data.get('specializations')
        if isinstance(specializations, list):
            stakeholder.set_specializations_list(specializations)

        # Handle current_projects
        projects = data.get('current_projects')
        if isinstance(projects, list):
            stakeholder.set_current_projects_list(projects)
        
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
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
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
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
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
        
        # Update additional fields that might be missing
        if 'job_title' in data:
            stakeholder.job_title = clean_optional(data.get('job_title'))
        
        if 'location' in data:
            stakeholder.location = clean_optional(data.get('location'))
        
        if 'linkedin_url' in data:
            stakeholder.linkedin_url = clean_optional(data.get('linkedin_url'))
        
        if 'twitter_handle' in data:
            stakeholder.twitter_handle = clean_optional(data.get('twitter_handle'))
        
        if 'education' in data:
            stakeholder.education = clean_optional(data.get('education'))
        
        if 'career_history' in data:
            stakeholder.career_history = clean_optional(data.get('career_history'))
        
        if 'hobbies' in data:
            stakeholder.hobbies = clean_optional(data.get('hobbies'))
        
        if 'family_info' in data:
            stakeholder.family_info = clean_optional(data.get('family_info'))
        
        if 'specializations' in data:
            specializations = data.get('specializations')
            if isinstance(specializations, list):
                stakeholder.set_specializations_list(specializations)
            elif isinstance(specializations, str):
                stakeholder.specializations = clean_optional(specializations)
        
        if 'current_projects' in data:
            projects = data.get('current_projects')
            if isinstance(projects, list):
                stakeholder.set_current_projects_list(projects)
            elif isinstance(projects, str):
                stakeholder.current_projects = clean_optional(projects)
        
        if 'trust_level' in data:
            try:
                trust_level = int(data['trust_level'])
                if 1 <= trust_level <= 10:
                    stakeholder.trust_level = trust_level
            except (ValueError, TypeError):
                pass  # Ignore invalid trust_level values
        
        if 'strategic_value' in data:
            valid_values = ['low', 'medium', 'high', 'critical']
            if data['strategic_value'] in valid_values:
                stakeholder.strategic_value = data['strategic_value']
        
        if 'timezone' in data:
            stakeholder.timezone = clean_optional(data.get('timezone'))
        
        if 'preferred_language' in data:
            stakeholder.preferred_language = clean_optional(data.get('preferred_language')) or 'English'
        
        if 'cultural_background' in data:
            stakeholder.cultural_background = clean_optional(data.get('cultural_background'))
        
        if 'preferred_communication_method' in data:
            stakeholder.preferred_communication_method = clean_optional(data.get('preferred_communication_method')) or 'email'
        
        if 'communication_frequency' in data:
            stakeholder.communication_frequency = clean_optional(data.get('communication_frequency')) or 'weekly'
        
        if 'best_contact_time' in data:
            stakeholder.best_contact_time = clean_optional(data.get('best_contact_time'))
        
        if 'communication_style' in data:
            stakeholder.communication_style = clean_optional(data.get('communication_style'))
        
        if 'seniority_level' in data:
            stakeholder.seniority_level = clean_optional(data.get('seniority_level'))
        
        if 'years_experience' in data:
            try:
                years = int(data['years_experience']) if data['years_experience'] else None
                stakeholder.years_experience = years
            except (ValueError, TypeError):
                pass
        
        if 'decision_making_authority' in data:
            valid_values = ['low', 'medium', 'high']
            if data['decision_making_authority'] in valid_values:
                stakeholder.decision_making_authority = data['decision_making_authority']
        
        if 'budget_authority' in data:
            valid_values = ['none', 'limited', 'significant', 'full']
            if data['budget_authority'] in valid_values:
                stakeholder.budget_authority = data['budget_authority']
        
        if 'availability_status' in data:
            valid_values = ['available', 'busy', 'unavailable']
            if data['availability_status'] in valid_values:
                stakeholder.availability_status = data['availability_status']
        
        if 'risk_level' in data:
            valid_values = ['low', 'medium', 'high']
            if data['risk_level'] in valid_values:
                stakeholder.risk_level = data['risk_level']
        
        if 'opportunity_potential' in data:
            valid_values = ['low', 'medium', 'high']
            if data['opportunity_potential'] in valid_values:
                stakeholder.opportunity_potential = data['opportunity_potential']
        
        if 'collaboration_history' in data:
            stakeholder.collaboration_history = clean_optional(data.get('collaboration_history'))
        
        if 'conflict_resolution_style' in data:
            stakeholder.conflict_resolution_style = clean_optional(data.get('conflict_resolution_style'))
        
        if 'other_social_links' in data:
            stakeholder.other_social_links = clean_optional(data.get('other_social_links'))
        
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
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
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
        # get_jwt_identity() returns a string, convert to int for database queries
        current_user_id = int(get_jwt_identity())
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
