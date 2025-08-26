import os.path
from sqlalchemy import create_engine, select
from sqlalchemy.orm import scoped_session, sessionmaker
from db.models import Base, Book
from contextlib import contextmanager
from config import settings
import json
from db.models import Book

engine = create_engine(settings.DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False))


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def load_books_if_empty():
    with session_scope() as session:
        if session.query(Book).count() == 0:
            with open(os.path.join('data', 'books_catalog.json'), encoding='utf-8') as file:
                books = json.load(file)
                books_object = [Book(
                    title=book['title'],
                    author=book["author"],
                    price=book["price"],
                    genre=book['genre'],
                    cover=book['cover'],
                    description=book['description'],
                    rating=book['rating'],
                    year=book['year']) for book in books]
                session.add_all(books_object)


def get_books_slice(genre: str, start_index: int = 0, window: int = 4):
    with session_scope() as session:
        find_books = session.execute(select(Book).where(Book.genre == genre)).scalars().all()
        books = [
            {"id": book.id, "title": book.title, "author": book.author, "price": book.price, "cover": book.cover,
             "genre": book.genre, "description": book.description, "rating": book.rating, "year": book.year}
            for book in find_books
        ]
        # вернём только "окно" в 5 штук
        return books[start_index:start_index + window]

