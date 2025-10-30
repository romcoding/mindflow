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
    family_info = db.Column(db.Text, nullable=True)  # Spouse, children, etc.
    hobbies = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    career_history = db.Column(db.Text, nullable=True)
    
    # Professional Details
    job_title = db.Column(db.String(100), nullable=True)
    seniority_level = db.Column(db.String(50), nullable=True)  # junior, mid, senior, executive
    years_experience = db.Column(db.Integer, nullable=True)
    specializations = db.Column(db.Text, nullable=True)  # Comma-separated skills/areas
    decision_making_authority = db.Column(db.String(50), default='low')  # low, medium, high
    budget_authority = db.Column(db.String(50), default='none')  # none, limited, significant, full
    
    # Geographic and Cultural
    location = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    preferred_language = db.Column(db.String(50), default='English')
    cultural_background = db.Column(db.String(100), nullable=True)
    
    # Communication Preferences
    preferred_communication_method = db.Column(db.String(50), default='email')  # email, phone, slack, etc.
    communication_frequency = db.Column(db.String(50), default='weekly')  # daily, weekly, monthly, as_needed
    best_contact_time = db.Column(db.String(100), nullable=True)  # e.g., "9-11 AM EST"
    communication_style = db.Column(db.String(50), nullable=True)  # formal, casual, direct, diplomatic
    
    # Network and Social
    linkedin_url = db.Column(db.String(200), nullable=True)
    twitter_handle = db.Column(db.String(50), nullable=True)
    other_social_links = db.Column(db.Text, nullable=True)  # JSON string
    
    # Project Context
    current_projects = db.Column(db.Text, nullable=True)  # Comma-separated project names
    availability_status = db.Column(db.String(50), default='available')  # available, busy, unavailable
    
    # Relationship Quality Metrics
    trust_level = db.Column(db.Integer, default=5)  # 1-10 scale
    collaboration_history = db.Column(db.Text, nullable=True)
    conflict_resolution_style = db.Column(db.String(50), nullable=True)
    
    # Strategic Importance
    strategic_value = db.Column(db.String(50), default='medium')  # low, medium, high, critical
    risk_level = db.Column(db.String(50), default='low')  # low, medium, high
    opportunity_potential = db.Column(db.String(50), default='medium')  # low, medium, high
    
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

    def get_specializations_list(self):
        """Convert comma-separated specializations string to list"""
        if self.specializations:
            return [spec.strip() for spec in self.specializations.split(',') if spec.strip()]
        return []
    
    def set_specializations_list(self, spec_list):
        """Convert list of specializations to comma-separated string"""
        if spec_list:
            self.specializations = ', '.join([spec.strip() for spec in spec_list if spec.strip()])
        else:
            self.specializations = None
    
    def get_current_projects_list(self):
        """Convert comma-separated projects string to list"""
        if self.current_projects:
            return [proj.strip() for proj in self.current_projects.split(',') if proj.strip()]
        return []
    
    def set_current_projects_list(self, proj_list):
        """Convert list of projects to comma-separated string"""
        if proj_list:
            self.current_projects = ', '.join([proj.strip() for proj in proj_list if proj.strip()])
        else:
            self.current_projects = None
    
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
            'family_info': self.family_info,
            'hobbies': self.hobbies,
            'education': self.education,
            'career_history': self.career_history,
            'job_title': self.job_title,
            'seniority_level': self.seniority_level,
            'years_experience': self.years_experience,
            'specializations': self.get_specializations_list(),
            'decision_making_authority': self.decision_making_authority,
            'budget_authority': self.budget_authority,
            'location': self.location,
            'timezone': self.timezone,
            'preferred_language': self.preferred_language,
            'cultural_background': self.cultural_background,
            'preferred_communication_method': self.preferred_communication_method,
            'communication_frequency': self.communication_frequency,
            'best_contact_time': self.best_contact_time,
            'communication_style': self.communication_style,
            'linkedin_url': self.linkedin_url,
            'twitter_handle': self.twitter_handle,
            'other_social_links': self.other_social_links,
            'current_projects': self.get_current_projects_list(),
            'availability_status': self.availability_status,
            'trust_level': self.trust_level,
            'collaboration_history': self.collaboration_history,
            'conflict_resolution_style': self.conflict_resolution_style,
            'strategic_value': self.strategic_value,
            'risk_level': self.risk_level,
            'opportunity_potential': self.opportunity_potential,
            'sentiment': self.sentiment,
            'influence': self.influence,
            'interest': self.interest,
            'tags': self.get_tags_list(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_contact': self.last_contact.isoformat() if self.last_contact else None
        }
