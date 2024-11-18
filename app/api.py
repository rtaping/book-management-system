# app/api.py
from sqlite3 import IntegrityError
from flask_restx import Api, Resource, fields, Namespace
from flask import request
from flask_login import current_user, login_required
from app import app, db
from app.models.book import Book
from app.services.ai_service import AIRecommendationService

api = Api(app, version='1.0', 
    title='Book Management API',
    description='Book management API with AI recommendations',
    doc='/api/docs'
)

books_ns = api.namespace('api/books', description='Book operations')
ai_ns = api.namespace('api/ai', description='AI recommendations')

book_model = api.model('Book', {
    'id': fields.Integer(readonly=True, description='Book unique identifier'),
    'title': fields.String(required=True, description='Book title'),
    'author': fields.String(required=True, description='Book author'),
    'isbn': fields.String(required=True, description='Book ISBN'),
    'year': fields.Integer(required=True, description='Publication year'),
    'genre': fields.String(description='Book genre'),
    'user_id': fields.Integer(readonly=True, description='User ID')
})

preference_model = api.model('Preferences', {
    'genres': fields.List(fields.String, description='List of preferred book genres', 
                         example=['fantasy', 'science fiction']),
    'authors': fields.List(fields.String, description='List of favorite authors', 
                          example=['Brandon Sanderson', 'Neil Gaiman'])
})

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

@books_ns.route('/')
class BookList(Resource):
    @books_ns.doc('list_books')
    @books_ns.marshal_list_with(book_model)
    @login_required
    def get(self):
        """List all books"""
        return Book.query.filter_by(user_id=current_user.id).all()

    @books_ns.doc('create_book')
    @books_ns.expect(book_model)
    @books_ns.marshal_with(book_model, code=201)
    @login_required
    def post(self):
        """Create a new book"""
        data = request.json
        # Check for existing ISBN for the current user
        existing_book = Book.query.filter_by(isbn=data['isbn'], user_id=current_user.id).first()
        if existing_book:
            api.abort(400, f"Book with ISBN {data['isbn']} already exists for this user.")
        book = Book(
            title=data['title'],
            author=data['author'],
            isbn=data['isbn'],
            year=data['year'],
            genre=data.get('genre', ''),
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        return book, 201

@books_ns.route('/<int:id>')
@books_ns.response(404, 'Book not found')
class BookItem(Resource):
    @books_ns.doc('get_book')
    @books_ns.marshal_with(book_model)
    @login_required
    def get(self, id):
        """Get a book by ID"""
        book = Book.query.get_or_404(id)
        if book.user_id != current_user.id:
            api.abort(403, 'Not authorized to access this book.')
        return book
    
    @books_ns.expect(book_model)
    @books_ns.marshal_with(book_model)
    @login_required
    def put(self, id):
        """Update a book"""
        book = Book.query.get_or_404(id)
        if book.user_id != current_user.id:
            api.abort(403, "Not authorized to update this book.")

        data = request.json
        
        # Check if ISBN changed and already exists for the current user
        if data['isbn'] != book.isbn:
            existing_book = Book.query.filter_by(isbn=data['isbn'], user_id=current_user.id).first()
            if existing_book:
                api.abort(400, f"Book with ISBN {data['isbn']} already exists for this user.")

        try:
            book.title = data['title']
            book.author = data['author']
            book.isbn = data['isbn']
            book.year = data['year']
            book.genre = data.get('genre', '')
            db.session.commit()
            return book
        except Exception as e:
            db.session.rollback()
            api.abort(400, str(e))

    @books_ns.doc('delete_book')
    @books_ns.response(204, 'Book deleted')
    @login_required
    def delete(self, id):
        """Delete a book"""
        book = Book.query.get_or_404(id)
        if book.user_id != current_user.id:
            api.abort(403, "Not authorized to delete this book.")
        db.session.delete(book)
        db.session.commit()
        return '', 204

@ai_ns.route('/book-recommendation')
class BookRecommendation(Resource):
    @ai_ns.doc('get_recommendations',
        responses={
            200: ('Success', recommendation_response),
            400: 'Validation Error',
            401: 'Unauthorized',
            429: 'Too Many Requests',
            500: 'Server Error'
        })
    @ai_ns.expect(preference_model)
    @ai_ns.marshal_with(recommendation_response)
    @login_required
    def post(self):
        """Get AI-powered book recommendations based on user preferences"""
        try:
            if not request.is_json:
                api.abort(400, "Request must be JSON")

            data = request.json
            
            if not isinstance(data.get('genres', []), list) or \
               not isinstance(data.get('authors', []), list):
                api.abort(400, "genres and authors must be arrays")
                
            if not data.get('genres') and not data.get('authors'):
                api.abort(400, "At least one genre or author required")

            recommendations = AIRecommendationService().get_recommendations(data)
            
            return {
                'success': True,
                'recommendations': recommendations,
                'message': f'Generated {len(recommendations)} recommendations'
            }
        except Exception as e:
            api.abort(500, str(e))