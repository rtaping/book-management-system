# app/celery_app.py - Celery task queue configuration and initialization
# Celery worker may need administrative privileges in order to work correctly
# But I have not encountered that issue as seen in ../logs/celery_worker.log

# Third-party imports
from celery import Celery  # Distributed task queue
from flask import Flask  # Type hint for Flask app
from typing import Any  # Type hints

def make_celery(app: Flask) -> Celery:
    """
    Create and configure Celery instance with Flask app context
    
    Args:
        app: Flask application instance
    Returns:
        Configured Celery instance
    """
    # Initialize Celery with Redis backend/broker
    celery = Celery(
        app.import_name,  # Use Flask app name
        backend='redis://localhost:6379/0',  # Results storage
        broker='redis://localhost:6379/0'  # Message broker
    )

    # Update Celery config from Flask config
    celery.conf.update(app.config)

    # Create task subclass with app context
    class ContextTask(celery.Task):
        """Celery task that runs within Flask app context"""
        
        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            """Execute task within app context"""
            with app.app_context():  # Ensure database connections etc. are available
                return self.run(*args, **kwargs)  # Run the actual task

    # Use custom task class by default
    celery.Task = ContextTask
    return celery  # Return configured Celery instance