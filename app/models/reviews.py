from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    rating_id = Column(Integer, ForeignKey('ratings.id'))
    comment = Column(String)
    comment_date = Column(DateTime, default=datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')
    rating = relationship('Rating', back_populates='reviews')


class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    is_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='rating')
    product = relationship('Product', back_populates='rating')
