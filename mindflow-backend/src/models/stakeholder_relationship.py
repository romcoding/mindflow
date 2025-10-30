from src.models.user import db
from datetime import datetime

class StakeholderRelationship(db.Model):
    """Model for relationships between stakeholders"""
    __tablename__ = 'stakeholder_relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Source and target stakeholders
    source_stakeholder_id = db.Column(db.Integer, db.ForeignKey('stakeholder.id'), nullable=False)
    target_stakeholder_id = db.Column(db.Integer, db.ForeignKey('stakeholder.id'), nullable=False)
    
    # Relationship metadata
    relationship_type = db.Column(db.String(50), nullable=False)  # boss, employee, colleague, family, friend, client, etc.
    relationship_strength = db.Column(db.Integer, default=5)  # 1-10 scale
    direction = db.Column(db.String(20), default='bidirectional')  # bidirectional, source_to_target, target_to_source
    
    # Relationship context
    context = db.Column(db.String(100), nullable=True)  # project, department, family, etc.
    description = db.Column(db.Text, nullable=True)
    
    # Status tracking
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_stakeholder = db.relationship('Stakeholder', foreign_keys=[source_stakeholder_id], backref='outgoing_relationships')
    target_stakeholder = db.relationship('Stakeholder', foreign_keys=[target_stakeholder_id], backref='incoming_relationships')
    
    def __repr__(self):
        return f'<StakeholderRelationship {self.source_stakeholder_id} -> {self.target_stakeholder_id} ({self.relationship_type})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_stakeholder_id': self.source_stakeholder_id,
            'target_stakeholder_id': self.target_stakeholder_id,
            'relationship_type': self.relationship_type,
            'relationship_strength': self.relationship_strength,
            'direction': self.direction,
            'context': self.context,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StakeholderInteraction(db.Model):
    """Model for tracking interactions with stakeholders"""
    __tablename__ = 'stakeholder_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stakeholder_id = db.Column(db.Integer, db.ForeignKey('stakeholder.id'), nullable=False)
    
    # Interaction details
    interaction_type = db.Column(db.String(50), nullable=False)  # meeting, call, email, message, etc.
    interaction_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=True)
    
    # Content and context
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.Text, nullable=True)
    
    # Sentiment and quality
    sentiment = db.Column(db.String(20), default='neutral')  # positive, neutral, negative
    quality_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    
    # Follow-up tracking
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    follow_up_completed = db.Column(db.Boolean, default=False)
    
    # Metadata
    location = db.Column(db.String(100), nullable=True)
    attendees = db.Column(db.Text, nullable=True)  # JSON string of attendee names
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stakeholder = db.relationship('Stakeholder', backref='interactions')
    
    def __repr__(self):
        return f'<StakeholderInteraction {self.title} with {self.stakeholder_id}>'
    
    def get_tags_list(self):
        """Convert comma-separated tags string to list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_list(self, tags_list):
        """Convert list of tags to comma-separated string"""
        if tags_list:
            self.tags = ', '.join([tag.strip() for tag in tags_list if tag.strip()])
        else:
            self.tags = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stakeholder_id': self.stakeholder_id,
            'interaction_type': self.interaction_type,
            'interaction_date': self.interaction_date.isoformat() if self.interaction_date else None,
            'duration_minutes': self.duration_minutes,
            'title': self.title,
            'description': self.description,
            'outcome': self.outcome,
            'sentiment': self.sentiment,
            'quality_rating': self.quality_rating,
            'follow_up_required': self.follow_up_required,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'follow_up_completed': self.follow_up_completed,
            'location': self.location,
            'attendees': self.attendees,
            'tags': self.get_tags_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
