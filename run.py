# run.py - Flask application entry point and database initialization

# Third-party imports
from flask import Flask  # Web framework
from app import app, db  # Import Flask app and database instances

# Main execution block
if __name__ == '__main__':
    # Initialize database tables
    with app.app_context():
        db.create_all()  # Create all defined models
    
    # Start Flask development server
    # Has been set to debug=False to test system as a regular user
    app.run(debug=False)