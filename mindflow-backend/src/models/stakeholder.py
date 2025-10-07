from src.models.user import db
from datetime import datetime

class Stakeholder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Basic Information
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    
    # Professional Information
    company = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    work_style = db.Column(db.Text, nullable=True)
    
    # Contact Information
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Personal Information
    birthday = db.Column(db.String(10), nullable=True)  # Store as YYYY-MM-DD string
    personal_notes = db.Column(db.Text, nullable=True)
    
    # Relationship Mapping
    sentiment = db.Column(db.String(20), default='neutral')  # positive, neutral, negative
    influence = db.Column(db.Integer, default=5)  # 1-10 scale
    interest = db.Column(db.Integer, default=5)   # 1-10 scale
    
    # Tags (stored as comma-separated string)
    tags = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact = db.Column(db.DateTime, nullable=True)

    # Relationships
    tasks = db.relationship('Task', backref='stakeholder', lazy=True)

    def __repr__(self):
        return f'<Stakeholder {self.name}>'

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
            'name': self.name,
            'role': self.role,
            'company': self.company,
            'department': self.department,
            'work_style': self.work_style,
            'email': self.email,
            'phone': self.phone,
            'birthday': self.birthday,
            'personal_notes': self.personal_notes,
            'sentiment': self.sentiment,
            'influence': self.influence,
            'interest': self.interest,
            'tags': self.get_tags_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_contact': self.last_contact.isoformat() if self.last_contact else None
        }
