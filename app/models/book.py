# app/models/book.py
from app import db
from datetime import datetime, timezone
from typing import Dict, Optional

class Book(db.Model):
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Required fields
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    
    # Optional fields
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(13), unique=True, nullable=True)  # Standard ISBN-13 length
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

    def to_dict(self) -> Dict:
        """Convert book to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'year': self.year,
            'isbn': self.isbn,
            'genre': self.genre,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }