# app/routes.py - Flask route handlers and controller logic

# Standard library imports
import re  # Regular expressions for validation
import os  # Operating system utilities

# Third-party imports
from flask import abort, render_template, redirect, url_for, flash, request, jsonify  # Flask web framework
from flask_login import login_user, logout_user, login_required, current_user  # User session management
from flask_limiter import Limiter  # API rate limiting
from flask_limiter.util import get_remote_address  # Client IP detection
from dotenv import load_dotenv  # Environment variable loading

# Local imports
from app import app, db  # Flask app and database
from app.models.user import User  # User model
from app.models.book import Book  # Book model
from app.tasks import send_contact_email, send_registration_email  # Async email tasks
from app.services.ai_service import AIRecommendationService  # AI recommendations

# Global variables
books = []  # Temporary storage for books

# Service initialization
# This limiter uses in-memory storage for rate limiting only to demonstrate the concept.
limiter = Limiter(  # Rate limiter setup
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per hour"]
)

ai_service = AIRecommendationService()  # AI service initialization

# Basic page routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Contact form handling
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            # Extract form data
            name = request.form['name']  # Sender name
            email = request.form['email']  # Sender email
            message = request.form['message']  # Message content
            
            # Queue async email task
            send_contact_email.delay(name=name, email=email, message=message)
            
            flash('Thank you for your message! We will respond soon.')
            return redirect(url_for('contact'))
            
        except Exception as e:
            app.logger.error(f"Contact form error: {str(e)}")  # Log error
            flash('Sorry, there was an error sending your message. Please try again.')
            
    return render_template('contact.html')

# Password validation helper
def validate_password(password):
    if len(password) < 8:  # Length check
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):  # Uppercase check
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r"[a-z]", password):  # Lowercase check
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r"\d", password):  # Number check
        return False, "Password must contain at least one number"
        
    if not re.search(r"[ !@#$%&'()*+,-./[\\\]^_`{|}~"+r'"]', password):  # Special char check
        return False, "Password must contain at least one special character"
        
    return True, "Password is valid"

# User authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # Check if already logged in
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        password = request.form['password']
        
        # Validate password complexity
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return redirect(url_for('register'))
            
        # Check password confirmation
        if password != request.form['confirm_password']:
            flash('Passwords do not match')
            return redirect(url_for('register'))
            
        # Check username availability
        user = User.query.filter_by(username=request.form['username']).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
            
        # Create new user
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        send_registration_email.delay(user.email, user.username)
        
        flash('Registration successful! Check your email for confirmation.')
        return redirect(url_for('login'))
        
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Check if already logged in
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Verify credentials
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()  # End user session
    flash('You have been successfully logged out.')
    return redirect(url_for('home'))

# Book CRUD operations
@app.route('/books')
@login_required
def books_list():
    # Get user's books
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('books/list.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        try:
            # Check for duplicate ISBN if provided
            isbn = request.form.get('isbn')
            if isbn and Book.query.filter_by(isbn=isbn).first():
                flash('A book with this ISBN already exists')
                return redirect(url_for('add_book')), 400

            book = Book(
                title=request.form['title'],
                author=request.form['author'],
                year=request.form['year'],
                isbn=isbn,
                genre=request.form['genre'],
                user_id=current_user.id
            )
            db.session.add(book)
            db.session.commit()
            return redirect(url_for('books_list'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding book')
            return redirect(url_for('add_book')), 400
    return render_template('books/add.html')

@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    book = Book.query.get_or_404(id)  # Get book or 404
    if book.user_id != current_user.id:  # Check ownership
        abort(403)
    if request.method == 'POST':
        # Update book details
        book.title = request.form['title']
        book.author = request.form['author']
        book.year = request.form['year']
        book.isbn = request.form['isbn']
        book.genre = request.form['genre']
        db.session.commit()
        return redirect(url_for('books_list'))
    return render_template('books/edit.html', book=book)

@app.route('/books/delete/<int:id>')
@login_required
def delete_book(id):
    book = Book.query.get_or_404(id)  # Get book or 404
    if book.user_id != current_user.id:  # Check ownership
        abort(403)
    db.session.delete(book)  # Delete book
    db.session.commit()
    return redirect(url_for('books_list'))

# AI recommendation API endpoint
@app.route('/api/ai/book-recommendation', methods=['POST'])
@limiter.limit("5 per minute")  # Rate limiting
@login_required  # Authentication required
def get_book_recommendations():
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        
        # Validate data types
        if not isinstance(data.get('genres', []), list) or \
           not isinstance(data.get('authors', []), list):
            return jsonify({"error": "genres and authors must be arrays"}), 400

        # Check required preferences
        if not data.get('genres') and not data.get('authors'):
            return jsonify({"error": "At least one genre or author required"}), 400

        # Get AI recommendations
        recommendations = ai_service.get_recommendations({
            'genres': data.get('genres', []),
            'authors': data.get('authors', []),
            'user_id': current_user.id
        })

        # Return successful response
        return jsonify({
            "success": True,
            "recommendations": recommendations,
            "message": f"Generated {len(recommendations)} recommendations"
        })

    except ValueError as e:
        # Handle validation errors
        app.logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        # Handle unexpected errors
        app.logger.error(f"Recommendation error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to get recommendations",
            "message": str(e)
        }), 500