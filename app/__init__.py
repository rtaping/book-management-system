# app/__init__.py - Flask application factory and configuration

# Third-party imports
from flask import Flask  # Web framework
from flask_sqlalchemy import SQLAlchemy  # Database ORM
from flask_login import LoginManager  # User session management
from .celery_app import make_celery  # Async task queue
import secrets  # Secure token generation

# Initialize Flask application instance
app = Flask(__name__)

# Application configuration settings
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'  # Database location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable expensive tracking

# Celery task queue configuration
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Redis message broker
    result_backend='redis://localhost:6379/0',  # Redis result storage
    broker_connection_retry_on_startup=True,  # Enable retry on startup
    broker_connection_max_retries=None,  # Retry indefinitely
    broker_connection_retry=True,  # Enable connection retry
    broker_connection_retry_delay=5  # 5 seconds between retries
)

# Initialize Flask extensions
db = SQLAlchemy(app)  # Database handler
login_manager = LoginManager(app)  # User session manager
login_manager.login_view = 'login'  # Redirect unauthorized users to login
login_manager.login_message_category = 'info'  # Flash message category
celery = make_celery(app)  # Task queue handler

# Import routes after app initialization to avoid circular imports
from app import routes, errors, models, api  # Register blueprints and models