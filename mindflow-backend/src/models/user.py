from src.models.db import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # Nullable for OAuth users
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    # OAuth fields
    oauth_provider = db.Column(db.String(20), nullable=True)  # 'google', 'github', etc.
    oauth_provider_id = db.Column(db.String(255), nullable=True)  # Provider's user ID
    avatar_url = db.Column(db.String(500), nullable=True)  # Profile picture URL from OAuth
    # Telegram integration
    telegram_chat_id = db.Column(db.String(50), nullable=True, unique=True)  # Telegram chat ID for persistent linking

    # Relationships
    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    stakeholders = db.relationship('Stakeholder', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set the user's password"""
        if password:
            self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        if not self.password_hash:
            return False  # OAuth users don't have passwords
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @classmethod
    def find_or_create_oauth_user(cls, provider, provider_id, email, username=None, first_name=None, last_name=None, avatar_url=None):
        """Find existing OAuth user or create a new one"""
        # Try to find by provider and provider_id first
        user = cls.query.filter_by(oauth_provider=provider, oauth_provider_id=provider_id).first()
        if user:
            # Update user info in case it changed
            if email and user.email != email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if avatar_url:
                user.avatar_url = avatar_url
            db.session.commit()
            return user
        
        # Try to find by email (account linking)
        user = cls.query.filter_by(email=email).first()
        if user:
            # Link OAuth to existing account
            user.oauth_provider = provider
            user.oauth_provider_id = provider_id
            if avatar_url:
                user.avatar_url = avatar_url
            db.session.commit()
            return user
        
        # Create new user
        if not username:
            username = email.split('@')[0]
        # Ensure username is unique
        base_username = username
        counter = 1
        while cls.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = cls(
            username=username,
            email=email,
            password_hash=None,  # OAuth users don't need passwords
            first_name=first_name,
            last_name=last_name,
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            avatar_url=avatar_url
        )
        db.session.add(user)
        db.session.commit()
        return user

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'oauth_provider': self.oauth_provider,
            'avatar_url': self.avatar_url
        }

    def to_public_dict(self):
        """Return user data without sensitive information"""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
