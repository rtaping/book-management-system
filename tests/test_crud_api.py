# tests/test_api_crud.py
# tested with: "pytest tests/test_crud_api.py -v > logs/pytest.log"

import pytest
from app import app, db
from app.models.user import User
from app.models.book import Book
from flask import url_for

@pytest.fixture(scope='function')
def test_client():
    """Set up a test client with an in-memory database."""
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'LOGIN_DISABLED': False,
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def test_user():
    """Create a test user."""
    with app.app_context():
        # Check if the user already exists and remove if necessary
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()

        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        yield user
        # Clean up after test
        db.session.delete(user)
        db.session.commit()

@pytest.fixture(scope='function')
def authenticated_client(test_client, test_user):
    """Log in the test user."""
    with test_client:
        response = test_client.post('/login', data={
            'username': test_user.username,
            'password': 'Password123!'
        }, follow_redirects=True)
        assert response.status_code == 200
        yield test_client

def test_create_book(authenticated_client):
    """Test creating a new book."""
    book_data = {
        'title': 'Sample Book',
        'author': 'Author Name',
        'isbn': '1234567890123',
        'year': 2021,
        'genre': 'Fiction'
    }
    response = authenticated_client.post('/api/books/', json=book_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == book_data['title']
    assert data['author'] == book_data['author']

def test_read_books(authenticated_client, test_user):
    """Test reading the list of books."""
    with app.app_context():
        # Add a sample book to the database
        book = Book(
            title='Existing Book',
            author='Existing Author',
            isbn='9876543210123',
            year=2020,
            genre='Non-Fiction',
            user_id=test_user.id
        )
        db.session.add(book)
        db.session.commit()

    response = authenticated_client.get('/api/books/')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Existing Book'

def test_update_book(authenticated_client, test_user):
    """Test updating an existing book."""
    with app.app_context():
        # Add a book to update
        book = Book(
            title='Old Title',
            author='Old Author',
            isbn='5555555555555',
            year=2019,
            genre='History',
            user_id=test_user.id
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    updated_data = {
        'title': 'Updated Title',
        'author': 'Updated Author',
        'isbn': '5555555555555',
        'year': 2022,
        'genre': 'Biography'
    }

    response = authenticated_client.put(f'/api/books/{book_id}', json=updated_data)
    assert response.status_code == 200
    data = response.get_json()
    assert data['title'] == updated_data['title']
    assert data['author'] == updated_data['author']
    assert data['year'] == updated_data['year']
    print("\n✓ Successfully updated book")

def test_delete_book(authenticated_client, test_user):
    """Test deleting a book."""
    with app.app_context():
        # Add a book to delete
        book = Book(
            title='Book to Delete',
            author='Author',
            isbn='4444444444444',
            year=2018,
            genre='Science',
            user_id=test_user.id
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

    response = authenticated_client.delete(f'/api/books/{book_id}')
    assert response.status_code == 204

    # Verify the book was deleted
    with app.app_context():
        deleted_book = Book.query.get(book_id)
        assert deleted_book is None