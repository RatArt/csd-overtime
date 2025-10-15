"""
Database models for the Overtime Management application.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo

db = SQLAlchemy()

# Timezone configuration
TIMEZONE = ZoneInfo('Europe/Prague')

def get_current_time():
    """Get current time in Czech timezone."""
    return datetime.now(TIMEZONE)


class User(UserMixin, db.Model):
    """
    User model - stores user information and authentication data.

    Attributes:
        id: Primary key
        username: Unique username for login
        password_hash: Hashed password
        user_type: 'admin' or 'common'
        group_id: Foreign key to Group
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default='common')  # 'admin' or 'common'
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    # Relationships
    group = db.relationship('Group', back_populates='users')
    overtime_records = db.relationship('Overtime', back_populates='user', cascade='all, delete-orphan')
    managed_groups = db.relationship('AdminGroup', back_populates='admin', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is an admin."""
        return self.user_type == 'admin'

    def can_manage_group(self, group_id):
        """Check if admin can manage a specific group."""
        if not self.is_admin():
            return False
        return any(ag.group_id == group_id for ag in self.managed_groups)

    def get_managed_group_ids(self):
        """Get list of group IDs this admin can manage."""
        if not self.is_admin():
            return []
        return [ag.group_id for ag in self.managed_groups]


class Group(db.Model):
    """
    Group model - stores team/department groups.

    Attributes:
        id: Primary key
        name: Group name
    """
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Relationships
    users = db.relationship('User', back_populates='group')
    admins = db.relationship('AdminGroup', back_populates='group', cascade='all, delete-orphan')


class AdminGroup(db.Model):
    """
    AdminGroup model - maps which groups each admin can manage.

    Attributes:
        id: Primary key
        admin_id: Foreign key to User (admin)
        group_id: Foreign key to Group
    """
    __tablename__ = 'admin_groups'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    # Relationships
    admin = db.relationship('User', back_populates='managed_groups')
    group = db.relationship('Group', back_populates='admins')

    # Ensure unique admin-group pairs
    __table_args__ = (db.UniqueConstraint('admin_id', 'group_id', name='unique_admin_group'),)


class Overtime(db.Model):
    """
    Overtime model - stores overtime entries for users.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        date: Date of overtime work
        minutes: Duration in minutes
        description: Description of work done
        created_at: Timestamp when record was created
    """
    __tablename__ = 'overtime'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    minutes = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=get_current_time)

    # Relationships
    user = db.relationship('User', back_populates='overtime_records')

    def get_hours_formatted(self):
        """Return overtime duration as formatted string (hours and minutes)."""
        hours = self.minutes // 60
        mins = self.minutes % 60
        return f"{hours}h {mins}m"
