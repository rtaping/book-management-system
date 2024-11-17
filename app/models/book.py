# app/models/book.py
from app import db
from datetime import datetime, timezone
from typing import Optional

class Book(db.Model):
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Required fields
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    
    # Optional fields
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(13), unique=True, nullable=True) # Standard ISBN-13 length
    genre = db.Column(db.String(50))
    
    # Metadata
    created_at = db.Column(
        db.DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        """Return string representation of Book."""
        return f'<Book {self.title}>'