from src.models.user import db
from datetime import datetime

class TaskCategory(db.Model):
    """Model for task categories and projects"""
    __tablename__ = 'task_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Category details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color code
    icon = db.Column(db.String(50), nullable=True)  # Icon name from Lucide
    
    # Category type and organization
    category_type = db.Column(db.String(50), default='project')  # project, area, goal, context
    parent_category_id = db.Column(db.Integer, db.ForeignKey('task_categories.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('EnhancedTask', backref='category', lazy=True)
    subcategories = db.relationship('TaskCategory', backref=db.backref('parent_category', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f'<TaskCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'category_type': self.category_type,
            'parent_category_id': self.parent_category_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'is_archived': self.is_archived,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': len(self.tasks) if self.tasks else 0
        }

class EnhancedTask(db.Model):
    """Enhanced task model with advanced planning features"""
    __tablename__ = 'enhanced_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('task_categories.id'), nullable=True)
    
    # Basic task information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Task status and priority
    status = db.Column(db.String(50), default='todo')  # todo, in_progress, waiting, done, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    
    # Time management
    due_date = db.Column(db.DateTime, nullable=True)
    start_date = db.Column(db.DateTime, nullable=True)
    estimated_duration = db.Column(db.Integer, nullable=True)  # Minutes
    actual_duration = db.Column(db.Integer, nullable=True)  # Minutes
    
    # Advanced planning
    energy_level_required = db.Column(db.String(20), default='medium')  # low, medium, high
    context = db.Column(db.String(100), nullable=True)  # @home, @office, @computer, @phone, etc.
    difficulty = db.Column(db.Integer, default=3)  # 1-5 scale
    
    # Dependencies and relationships
    parent_task_id = db.Column(db.Integer, db.ForeignKey('enhanced_tasks.id'), nullable=True)
    depends_on_tasks = db.Column(db.Text, nullable=True)  # JSON array of task IDs
    blocks_tasks = db.Column(db.Text, nullable=True)  # JSON array of task IDs
    
    # Stakeholder connections
    assigned_stakeholder_id = db.Column(db.Integer, db.ForeignKey('stakeholder.id'), nullable=True)
    related_stakeholders = db.Column(db.Text, nullable=True)  # JSON array of stakeholder IDs
    
    # Progress tracking
    progress_percentage = db.Column(db.Integer, default=0)  # 0-100
    completion_notes = db.Column(db.Text, nullable=True)
    
    # Recurrence and repetition
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(100), nullable=True)  # daily, weekly, monthly, custom
    recurrence_end_date = db.Column(db.DateTime, nullable=True)
    
    # Tags and categorization
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags
    
    # Kanban board positioning
    board_column = db.Column(db.String(50), default='todo')  # todo, in_progress, review, done
    board_position = db.Column(db.Integer, default=0)  # Position within column
    
    # Time tracking
    time_spent = db.Column(db.Integer, default=0)  # Total minutes spent
    last_worked_on = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    source = db.Column(db.String(50), default='manual')  # manual, quick_add, import, recurring
    external_id = db.Column(db.String(100), nullable=True)  # For integrations
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    subtasks = db.relationship('EnhancedTask', backref=db.backref('parent_task', remote_side=[id]), lazy=True)
    assigned_stakeholder = db.relationship('Stakeholder', backref='assigned_tasks')
    
    def __repr__(self):
        return f'<EnhancedTask {self.title}>'
    
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
    
    def get_related_stakeholders_list(self):
        """Convert JSON string to list of stakeholder IDs"""
        import json
        if self.related_stakeholders:
            try:
                return json.loads(self.related_stakeholders)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_related_stakeholders_list(self, stakeholder_ids):
        """Convert list of stakeholder IDs to JSON string"""
        import json
        if stakeholder_ids:
            self.related_stakeholders = json.dumps(stakeholder_ids)
        else:
            self.related_stakeholders = None
    
    def get_depends_on_list(self):
        """Convert JSON string to list of task IDs"""
        import json
        if self.depends_on_tasks:
            try:
                return json.loads(self.depends_on_tasks)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_depends_on_list(self, task_ids):
        """Convert list of task IDs to JSON string"""
        import json
        if task_ids:
            self.depends_on_tasks = json.dumps(task_ids)
        else:
            self.depends_on_tasks = None
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ['done', 'cancelled']:
            return datetime.utcnow() > self.due_date
        return False
    
    def can_start(self):
        """Check if task can be started based on dependencies"""
        depends_on = self.get_depends_on_list()
        if not depends_on:
            return True
        
        # Check if all dependent tasks are completed
        from sqlalchemy import and_
        dependent_tasks = EnhancedTask.query.filter(
            and_(
                EnhancedTask.id.in_(depends_on),
                EnhancedTask.user_id == self.user_id
            )
        ).all()
        
        return all(task.status == 'done' for task in dependent_tasks)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'energy_level_required': self.energy_level_required,
            'context': self.context,
            'difficulty': self.difficulty,
            'parent_task_id': self.parent_task_id,
            'depends_on_tasks': self.get_depends_on_list(),
            'assigned_stakeholder_id': self.assigned_stakeholder_id,
            'related_stakeholders': self.get_related_stakeholders_list(),
            'progress_percentage': self.progress_percentage,
            'completion_notes': self.completion_notes,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'recurrence_end_date': self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            'tags': self.get_tags_list(),
            'board_column': self.board_column,
            'board_position': self.board_position,
            'time_spent': self.time_spent,
            'last_worked_on': self.last_worked_on.isoformat() if self.last_worked_on else None,
            'source': self.source,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue(),
            'can_start': self.can_start(),
            'subtask_count': len(self.subtasks) if self.subtasks else 0
        }
