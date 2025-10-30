from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db
from src.models.stakeholder_relationship import StakeholderRelationship, StakeholderInteraction
from src.models.stakeholder import Stakeholder
from datetime import datetime
import json

stakeholder_relationships_bp = Blueprint('stakeholder_relationships', __name__)

# Stakeholder Relationships Routes

@stakeholder_relationships_bp.route('/relationships', methods=['GET'])
@jwt_required()
def get_relationships():
    """Get all stakeholder relationships for the current user"""
    try:
        current_user_id = get_jwt_identity()
        relationships = StakeholderRelationship.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).all()
        
        return jsonify({
            'success': True,
            'relationships': [rel.to_dict() for rel in relationships]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_relationships_bp.route('/relationships', methods=['POST'])
@jwt_required()
def create_relationship():
    """Create a new stakeholder relationship"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['source_stakeholder_id', 'target_stakeholder_id', 'relationship_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Verify stakeholders belong to current user
        source_stakeholder = Stakeholder.query.filter_by(
            id=data['source_stakeholder_id'],
            user_id=current_user_id
        ).first()
        
        target_stakeholder = Stakeholder.query.filter_by(
            id=data['target_stakeholder_id'],
            user_id=current_user_id
        ).first()
        
        if not source_stakeholder or not target_stakeholder:
            return jsonify({'success': False, 'error': 'Invalid stakeholder IDs'}), 400
        
        # Check if relationship already exists
        existing = StakeholderRelationship.query.filter_by(
            user_id=current_user_id,
            source_stakeholder_id=data['source_stakeholder_id'],
            target_stakeholder_id=data['target_stakeholder_id'],
            is_active=True
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Relationship already exists'}), 400
        
        # Create new relationship
        relationship = StakeholderRelationship(
            user_id=current_user_id,
            source_stakeholder_id=data['source_stakeholder_id'],
            target_stakeholder_id=data['target_stakeholder_id'],
            relationship_type=data['relationship_type'],
            relationship_strength=data.get('relationship_strength', 5),
            direction=data.get('direction', 'bidirectional'),
            context=data.get('context'),
            description=data.get('description')
        )
        
        db.session.add(relationship)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'relationship': relationship.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_relationships_bp.route('/relationships/<int:relationship_id>', methods=['PUT'])
@jwt_required()
def update_relationship(relationship_id):
    """Update a stakeholder relationship"""
    try:
        current_user_id = get_jwt_identity()
        relationship = StakeholderRelationship.query.filter_by(
            id=relationship_id,
            user_id=current_user_id
        ).first()
        
        if not relationship:
            return jsonify({'success': False, 'error': 'Relationship not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        updatable_fields = [
            'relationship_type', 'relationship_strength', 'direction',
            'context', 'description', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(relationship, field, data[field])
        
        relationship.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'relationship': relationship.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_relationships_bp.route('/relationships/<int:relationship_id>', methods=['DELETE'])
@jwt_required()
def delete_relationship(relationship_id):
    """Delete a stakeholder relationship"""
    try:
        current_user_id = get_jwt_identity()
        relationship = StakeholderRelationship.query.filter_by(
            id=relationship_id,
            user_id=current_user_id
        ).first()
        
        if not relationship:
            return jsonify({'success': False, 'error': 'Relationship not found'}), 404
        
        # Soft delete by setting is_active to False
        relationship.is_active = False
        relationship.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Stakeholder Interactions Routes

@stakeholder_interactions_bp = Blueprint('stakeholder_interactions', __name__)

@stakeholder_interactions_bp.route('/interactions', methods=['GET'])
@jwt_required()
def get_interactions():
    """Get all stakeholder interactions for the current user"""
    try:
        current_user_id = get_jwt_identity()
        stakeholder_id = request.args.get('stakeholder_id')
        
        query = StakeholderInteraction.query.filter_by(user_id=current_user_id)
        
        if stakeholder_id:
            query = query.filter_by(stakeholder_id=stakeholder_id)
        
        interactions = query.order_by(StakeholderInteraction.interaction_date.desc()).all()
        
        return jsonify({
            'success': True,
            'interactions': [interaction.to_dict() for interaction in interactions]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_interactions_bp.route('/interactions', methods=['POST'])
@jwt_required()
def create_interaction():
    """Create a new stakeholder interaction"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['stakeholder_id', 'interaction_type', 'title', 'interaction_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Verify stakeholder belongs to current user
        stakeholder = Stakeholder.query.filter_by(
            id=data['stakeholder_id'],
            user_id=current_user_id
        ).first()
        
        if not stakeholder:
            return jsonify({'success': False, 'error': 'Invalid stakeholder ID'}), 400
        
        # Parse interaction date
        try:
            interaction_date = datetime.fromisoformat(data['interaction_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid interaction_date format'}), 400
        
        # Create new interaction
        interaction = StakeholderInteraction(
            user_id=current_user_id,
            stakeholder_id=data['stakeholder_id'],
            interaction_type=data['interaction_type'],
            interaction_date=interaction_date,
            title=data['title'],
            description=data.get('description'),
            duration_minutes=data.get('duration_minutes'),
            outcome=data.get('outcome'),
            sentiment=data.get('sentiment', 'neutral'),
            quality_rating=data.get('quality_rating'),
            follow_up_required=data.get('follow_up_required', False),
            location=data.get('location'),
            attendees=data.get('attendees')
        )
        
        # Handle tags
        if 'tags' in data:
            interaction.set_tags_list(data['tags'])
        
        # Handle follow-up date
        if data.get('follow_up_date'):
            try:
                follow_up_date = datetime.fromisoformat(data['follow_up_date'].replace('Z', '+00:00'))
                interaction.follow_up_date = follow_up_date
            except ValueError:
                pass
        
        db.session.add(interaction)
        
        # Update stakeholder's last contact date
        stakeholder.last_contact = interaction_date
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'interaction': interaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_interactions_bp.route('/interactions/<int:interaction_id>', methods=['PUT'])
@jwt_required()
def update_interaction(interaction_id):
    """Update a stakeholder interaction"""
    try:
        current_user_id = get_jwt_identity()
        interaction = StakeholderInteraction.query.filter_by(
            id=interaction_id,
            user_id=current_user_id
        ).first()
        
        if not interaction:
            return jsonify({'success': False, 'error': 'Interaction not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        updatable_fields = [
            'interaction_type', 'title', 'description', 'duration_minutes',
            'outcome', 'sentiment', 'quality_rating', 'follow_up_required',
            'follow_up_completed', 'location', 'attendees'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(interaction, field, data[field])
        
        # Handle date fields
        if 'interaction_date' in data:
            try:
                interaction_date = datetime.fromisoformat(data['interaction_date'].replace('Z', '+00:00'))
                interaction.interaction_date = interaction_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid interaction_date format'}), 400
        
        if 'follow_up_date' in data:
            if data['follow_up_date']:
                try:
                    follow_up_date = datetime.fromisoformat(data['follow_up_date'].replace('Z', '+00:00'))
                    interaction.follow_up_date = follow_up_date
                except ValueError:
                    return jsonify({'success': False, 'error': 'Invalid follow_up_date format'}), 400
            else:
                interaction.follow_up_date = None
        
        # Handle tags
        if 'tags' in data:
            interaction.set_tags_list(data['tags'])
        
        interaction.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'interaction': interaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_interactions_bp.route('/interactions/<int:interaction_id>', methods=['DELETE'])
@jwt_required()
def delete_interaction(interaction_id):
    """Delete a stakeholder interaction"""
    try:
        current_user_id = get_jwt_identity()
        interaction = StakeholderInteraction.query.filter_by(
            id=interaction_id,
            user_id=current_user_id
        ).first()
        
        if not interaction:
            return jsonify({'success': False, 'error': 'Interaction not found'}), 404
        
        db.session.delete(interaction)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Network Analysis Routes

@stakeholder_relationships_bp.route('/network/graph', methods=['GET'])
@jwt_required()
def get_network_graph():
    """Get stakeholder network graph data for visualization"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get all stakeholders for the user
        stakeholders = Stakeholder.query.filter_by(user_id=current_user_id).all()
        
        # Get all active relationships
        relationships = StakeholderRelationship.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).all()
        
        # Format nodes for D3.js
        nodes = []
        for stakeholder in stakeholders:
            nodes.append({
                'id': str(stakeholder.id),
                'name': stakeholder.name,
                'group': stakeholder.company or 'Unknown',
                'role': stakeholder.role,
                'sentiment': stakeholder.sentiment,
                'influence': stakeholder.influence,
                'interest': stakeholder.interest,
                'strategic_value': stakeholder.strategic_value,
                'trust_level': stakeholder.trust_level,
                'size': stakeholder.influence * 2,  # Node size based on influence
                'color': {
                    'positive': '#10B981',
                    'neutral': '#6B7280',
                    'negative': '#EF4444'
                }.get(stakeholder.sentiment, '#6B7280')
            })
        
        # Format links for D3.js
        links = []
        for rel in relationships:
            links.append({
                'source': str(rel.source_stakeholder_id),
                'target': str(rel.target_stakeholder_id),
                'relationship_type': rel.relationship_type,
                'strength': rel.relationship_strength,
                'context': rel.context,
                'direction': rel.direction,
                'value': rel.relationship_strength  # Link thickness
            })
        
        return jsonify({
            'success': True,
            'graph': {
                'nodes': nodes,
                'links': links
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@stakeholder_relationships_bp.route('/network/metrics', methods=['GET'])
@jwt_required()
def get_network_metrics():
    """Get network analysis metrics"""
    try:
        current_user_id = get_jwt_identity()
        
        # Basic counts
        total_stakeholders = Stakeholder.query.filter_by(user_id=current_user_id).count()
        total_relationships = StakeholderRelationship.query.filter_by(
            user_id=current_user_id,
            is_active=True
        ).count()
        
        # Sentiment distribution
        sentiment_counts = db.session.query(
            Stakeholder.sentiment,
            db.func.count(Stakeholder.id)
        ).filter_by(user_id=current_user_id).group_by(Stakeholder.sentiment).all()
        
        sentiment_distribution = {sentiment: count for sentiment, count in sentiment_counts}
        
        # Influence distribution
        high_influence = Stakeholder.query.filter(
            Stakeholder.user_id == current_user_id,
            Stakeholder.influence >= 8
        ).count()
        
        medium_influence = Stakeholder.query.filter(
            Stakeholder.user_id == current_user_id,
            Stakeholder.influence >= 5,
            Stakeholder.influence < 8
        ).count()
        
        low_influence = Stakeholder.query.filter(
            Stakeholder.user_id == current_user_id,
            Stakeholder.influence < 5
        ).count()
        
        # Recent interactions
        recent_interactions = StakeholderInteraction.query.filter(
            StakeholderInteraction.user_id == current_user_id,
            StakeholderInteraction.interaction_date >= datetime.utcnow().replace(day=1)  # This month
        ).count()
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_stakeholders': total_stakeholders,
                'total_relationships': total_relationships,
                'sentiment_distribution': sentiment_distribution,
                'influence_distribution': {
                    'high': high_influence,
                    'medium': medium_influence,
                    'low': low_influence
                },
                'recent_interactions': recent_interactions,
                'network_density': total_relationships / max(total_stakeholders * (total_stakeholders - 1) / 2, 1) if total_stakeholders > 1 else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
