# tests/test_book_management.py
import unittest
from app import app, db
from app.models.user import User
from app.models.book import Book
from app.services.ai_service import AIRecommendationService

class TestBookManagement(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test user
            self.test_user = User(username='testuser', email='test@example.com')
            self.test_user.set_password('Password123!')
            db.session.add(self.test_user)
            db.session.commit()  # Commit user first to get ID
            
            # Create test book with unique ISBN
            self.test_book = Book(
                title='Test Book',
                author='Test Author',
                isbn='1111111111111',  # Unique ISBN
                year=2024,
                genre='Fiction',
                user_id=self.test_user.id  # Use actual user ID
            )
            db.session.add(self.test_book)
            db.session.commit()

    def tearDown(self):
        """Cleanup test environment"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_creation(self):
        """Test user model"""
        with app.app_context():
            user = User.query.first()
            self.assertEqual(user.username, 'testuser')
            self.assertTrue(user.check_password('Password123!'))

    def test_book_creation(self):
        """Test book model"""
        with app.app_context():
            book = Book.query.first()
            self.assertEqual(book.title, 'Test Book')
            self.assertEqual(book.author, 'Test Author')

    def test_user_authentication(self):
        """Test login/logout functionality"""
        # Test login
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)

        # Test logout
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)

    def test_book_operations(self):
        """Test book CRUD operations"""
        # Login first
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'Password123!'
        })

        # Test book list
        response = self.client.get('/books')
        self.assertEqual(response.status_code, 200)

        # Test add book with unique ISBN
        response = self.client.post('/books/add', data={
            'title': 'New Book',
            'author': 'New Author',
            'isbn': '2222222222222',  # Different ISBN
            'year': '2024',
            'genre': 'Fiction'
        })
        self.assertEqual(response.status_code, 302)

        # Test add book with duplicate ISBN
        response = self.client.post('/books/add', data={
            'title': 'Another Book',
            'author': 'Another Author',
            'isbn': '2222222222222',  # Same ISBN as previous book
            'year': '2024',
            'genre': 'Fiction'
        })
        self.assertEqual(response.status_code, 400)

        # Test add book without ISBN
        response = self.client.post('/books/add', data={
            'title': 'No ISBN Book',
            'author': 'Some Author',
            'year': '2024',
            'genre': 'Fiction'
        })
        self.assertEqual(response.status_code, 302)

        # Test edit book with new ISBN
        response = self.client.post(f'/books/edit/{self.test_book.id}', data={
            'title': 'Updated Book',
            'author': 'Updated Author',
            'isbn': '3333333333333',  # Different ISBN
            'year': '2024',
            'genre': 'Fiction'
        })
        self.assertEqual(response.status_code, 302)

        # Test delete book
        response = self.client.get(f'/books/delete/{self.test_book.id}')
        self.assertEqual(response.status_code, 302)

    def test_ai_recommendations(self):
        """Test AI recommendation endpoint"""
        # Login first
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'Password123!'
        })

        response = self.client.post('/api/ai/book-recommendation',
            json={
                'genres': ['fantasy'],
                'authors': ['Tolkien']
            })
        self.assertEqual(response.status_code, 200)
        self.assertIn('recommendations', response.get_json())
        
        # Will display AssertionError: 500 != 401 as I do not have tokens for the OpenAI API (need to pay for it)
if __name__ == '__main__':
    unittest.main()