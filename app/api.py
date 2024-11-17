# app/api.py - RESTful API endpoints for book management and AI recommendations

# Third-party imports
from flask_restx import Api, Resource, fields, Namespace  # REST API utilities
from flask import request  # HTTP request handling
from flask_login import current_user, login_required  # Authentication
from app import app, db  # Flask app and database
from app.models.book import Book  # Book model
from app.services.ai_service import AIRecommendationService  # AI recommendations

# Initialize Swagger/OpenAPI documentation
api = Api(app, version='1.0', 
    title='Book Management API',
    description='Book management API with AI recommendations',
    doc='/api/docs'  # Swagger UI endpoint
)

# Create API namespaces for route organization
books_ns = api.namespace('api/books', description='Book operations')  # Book CRUD operations
ai_ns = api.namespace('api/ai', description='AI recommendations')  # AI features

# Define request/response models for API documentation
book_model = api.model('Book', {
    'id': fields.Integer(readonly=True, description='Book unique identifier'),
    'title': fields.String(required=True, description='Book title'),
    'author': fields.String(required=True, description='Book author'),
    'isbn': fields.String(required=True, description='Book ISBN'),
    'year': fields.Integer(required=True, description='Publication year'),
    'user_id': fields.Integer(readonly=True, description='User ID')
})

# AI recommendation request model
preference_model = api.model('Preferences', {
    'genres': fields.List(fields.String, description='List of preferred book genres', 
                         example=['fantasy', 'science fiction']),
    'authors': fields.List(fields.String, description='List of favorite authors', 
                          example=['Brandon Sanderson', 'Neil Gaiman'])
})

# AI recommendation response models
recommendation_model = api.model('Recommendation', {
    'title': fields.String(required=True, description='Book title'),
    'author': fields.String(required=True, description='Book author'),
    'description': fields.String(required=True, description='Book description'),
    'genre': fields.String(required=True, description='Book genre')
})

recommendation_response = api.model('RecommendationResponse', {
    'success': fields.Boolean(description='Operation success status'),
    'recommendations': fields.List(fields.Nested(recommendation_model)),
    'message': fields.String(description='Response message')
})

# Book CRUD operations
@books_ns.route('/')
class BookList(Resource):
    @books_ns.doc('list_books')  # Swagger documentation
    @books_ns.marshal_list_with(book_model)  # Response serialization
    @login_required  # Authentication required
    def get(self):
        """List all books for current user"""
        return Book.query.filter_by(user_id=current_user.id).all()

    @books_ns.doc('create_book')
    @books_ns.expect(book_model)  # Request validation
    @books_ns.marshal_with(book_model, code=201)  # Response with 201 Created
    @login_required
    def post(self):
        """Create a new book"""
        data = request.json
        book = Book(
            title=data['title'],
            author=data['author'],
            isbn=data['isbn'],
            year=data['year'],
            user_id=current_user.id  # Associate with current user
        )
        db.session.add(book)
        db.session.commit()
        return book, 201

# Single book operations with ID
@books_ns.route('/<int:id>')
@books_ns.response(404, 'Book not found')  # Error response
class BookItem(Resource):
    @books_ns.doc('get_book')
    @books_ns.marshal_with(book_model)
    @login_required
    def get(self, id):
        """Fetch a book by ID"""
        return Book.query.get_or_404(id)

    @books_ns.doc('update_book')
    @books_ns.expect(book_model)
    @books_ns.marshal_with(book_model)
    @login_required
    def put(self, id):
        """Update a book"""
        book = Book.query.get_or_404(id)  # Get book or 404
        if book.user_id != current_user.id:  # Check ownership
            api.abort(403, "Not authorized")
        data = request.json
        book.title = data['title']
        book.author = data['author']
        book.isbn = data['isbn']
        book.year = data['year']
        db.session.commit()
        return book

    @books_ns.doc('delete_book')
    @books_ns.response(204, 'Book deleted')
    @login_required
    def delete(self, id):
        """Delete a book"""
        book = Book.query.get_or_404(id)
        if book.user_id != current_user.id:
            api.abort(403, "Not authorized")
        db.session.delete(book)
        db.session.commit()
        return '', 204

# AI recommendation endpoint
@ai_ns.route('/book-recommendation')
class BookRecommendation(Resource):
    @ai_ns.doc('get_recommendations',
        responses={  # Document possible responses
            200: ('Success', recommendation_response),
            400: 'Validation Error',
            401: 'Unauthorized',
            429: 'Too Many Requests',
            500: 'Server Error'
        })
    @ai_ns.expect(preference_model)  # Expect preferences in request
    @ai_ns.marshal_with(recommendation_response)  # Format response
    @login_required
    def post(self):
        """Get AI-powered book recommendations based on user preferences"""
        try:
            # Validate request format
            if not request.is_json:
                api.abort(400, "Request must be JSON")

            data = request.json
            
            # Validate request data types
            if not isinstance(data.get('genres', []), list) or \
               not isinstance(data.get('authors', []), list):
                api.abort(400, "genres and authors must be arrays")
                
            # Ensure at least one preference provided
            if not data.get('genres') and not data.get('authors'):
                api.abort(400, "At least one genre or author required")

            # Get AI recommendations
            recommendations = AIRecommendationService().get_recommendations(data)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'message': f'Generated {len(recommendations)} recommendations'
            }
        except Exception as e:
            api.abort(500, str(e))  # Return 500 for unexpected errors