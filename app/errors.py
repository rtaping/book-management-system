# app/errors.py
from flask import render_template
from app import app

@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors"""
    return render_template('errors/400.html'), 400

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access errors"""
    return render_template('errors/401.html'), 401

@app.errorhandler(403)
def forbidden(e):
    """Handle forbidden access errors"""
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    """Handle page not found errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle internal server errors"""
    return render_template('errors/500.html'), 500