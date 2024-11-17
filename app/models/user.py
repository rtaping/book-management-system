# app/models/user.py

# External imports
from app import db, login_manager  # Database and login management
from flask_login import UserMixin  # User authentication mixin
from werkzeug.security import generate_password_hash, check_password_hash  # Password hashing
from typing import Optional, List  # Type hints

# User loader for Flask-Login
@login_manager.user_loader
def load_user(id: int) -> Optional['User']:
    """Load user by ID for Flask-Login."""
    return User.query.get(int(id))

# User model definition
class User(UserMixin, db.Model):
    """User model for authentication and book management."""

    # Database columns
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    username = db.Column(db.String(64), unique=True, nullable=False)  # Unique username
    email = db.Column(db.String(120), unique=True, nullable=False)  # Unique email
    password_hash = db.Column(db.String(128))  # Hashed password storage

    # Relationship definitions
    books = db.relationship(
        'Book',
        backref='owner',  # Adds owner property to Book model
        lazy='dynamic',  # Lazy loading for performance
        cascade='all, delete-orphan'  # Delete books when user is deleted
    )

    # Password management methods
    def set_password(self, password: str) -> None:
        """Hash and store password."""
        self.password_hash = generate_password_hash(password)  # Generate secure hash

    def check_password(self, password: str) -> bool:
        """Verify password matches hash."""
        return check_password_hash(self.password_hash, password)  # Compare hash

    # String representation
    def __repr__(self) -> str:
        """Display format for debugging."""
        return f'<User {self.username}>'  # Show username in logs