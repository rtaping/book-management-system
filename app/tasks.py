# app/tasks.py - Celery async task definitions for email handling

# Third-party imports
from app import app, celery  # Flask app and Celery instance
from time import sleep  # For simulating delays

@celery.task
def send_registration_email(user_email, username):
    """Mock function to simulate sending registration email"""
    
    # Simulate network delay
    sleep(5)  # 5 second delay
    
    # Mock email sending process
    print(f"Sending registration email to {user_email}")  # Log recipient
    print(f"Subject: Welcome to Book Management System")  # Log subject
    print(f"Dear {username},\n\nThank you for registering!")  # Log content
    
    return True  # Indicate success

@celery.task
def send_contact_email(name: str, email: str, message: str):
    """Send contact form email (mock implementation)"""
    
    # Log contact form submission
    print(f"Sending contact email from {name} ({email})")  # Log sender
    print(f"Message: {message}")  # Log message content
    
    return True  # Indicate success