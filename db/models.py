from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date,func,Boolean
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    email = Column(String(100), unique=True)
    password_hash = Column(String(256))

    reviews = relationship("Review", back_populates="user")
    cartitems = relationship("Cartitem", back_populates="user")
    order = relationship("Order", back_populates="user")
    is_confirmed = Column(Boolean, default=False)  # подтверждение
    sms_code = Column(String(6), nullable=True)


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    author = Column(String(30))
    price = Column(Float)
    genre = Column(String(30), nullable=True)
    cover = Column(String(256))
    description = Column(String(10000))
    rating = Column(Float)
    year = Column(Integer, nullable=True)

    cartitems = relationship("Cartitem", back_populates="book")
    reviews = relationship("Review", back_populates="book")
    orderitems = relationship("Orderitem", back_populates='book')


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    description = Column(String(10000), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    rating = Column(Integer, nullable=True)

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")


class Cartitem(Base):
    __tablename__ = 'cartitems'

    # CartItem: пользователь, книга, количество
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    quantity = Column(Integer, nullable=True)

    user = relationship("User", back_populates='cartitems')
    book = relationship("Book", back_populates='cartitems')


class Orderitem(Base):
    # OrderItem: книга, количество, цена
    __tablename__ = 'orderitems'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer,ForeignKey('orders.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    quantity = Column(Integer, nullable=True)

    book = relationship("Book", back_populates='orderitems')
    order = relationship("Order", back_populates='orderitems')


# Order: пользователь, дата, статус, адрес, список книг

class Order(Base):
    # OrderItem: книга, количество, цена
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date,default=func.current_date())
    status = Column(Integer, default=0)  # можно хранить состояние заказа
    address = Column(String,default='Самовывоз')

    orderitems = relationship("Orderitem", back_populates='order')
    user = relationship("User", back_populates='order')
