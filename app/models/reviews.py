from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    comment = Column(String)
    is_active = Column(Boolean, default=True)
    comment_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    rating_id = Column(Integer, ForeignKey('ratings.id'))

    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')
    ratings = relationship('Rating', back_populates='reviews')


class Rating(Base):
    __tablename__ = 'ratings'
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='uix_user_product'),)

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='ratings')
    product = relationship('Product', back_populates='ratings')
    reviews = relationship('Review', back_populates='ratings')
