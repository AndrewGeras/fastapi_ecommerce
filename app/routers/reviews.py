from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.schemas import CreateReview
from app.models import User, Product, Review, Rating
from .auth import get_current_user

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).where(Review.is_active == True))
    if reviews:
        return reviews.all()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="There are no reviews"
    )


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                           product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This product is not found"
        )

    reviews_set = await db.scalars(
        select(Review).where(Review.product_id == product.id, Review.is_active == True)
    )
    reviews = reviews_set.all()

    if reviews:
        return reviews

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="There's no reviews"
    )


@router.post('/{product_slug}')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     product_slug: str,
                     review: CreateReview,
                     get_user: Annotated[dict, Depends(get_current_user)]):

    if not get_user.get("is_customer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can leave reviews"
        )

    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This product is not found"
        )

    new_rating = {'grade': review.rating_grade,
                  'user_id': get_user.get('id'),
                  'product_id': product.id}

    await db.execute(
        insert(Rating).values(new_rating).on_conflict_do_update(constraint='uc_rating_user_product',
                                                                set_={'grade': new_rating['grade'],
                                                                      'is_active': True}))
    await db.commit()

    rating = await db.scalar(select(Rating).where(Rating.user_id == get_user.get('id'),
                                                  Rating.product_id == product.id,
                                                  ))
    new_review = {'comment': review.comment,
                  'user_id': get_user.get('id'),
                  'product_id': product.id,
                  'rating_id': rating.id}
    await db.execute(
        insert(Review).values(new_review).on_conflict_do_update(constraint='uc_review_user_product',
                                                                set_={'comment': new_review['comment'],
                                                                      'rating_id': new_review['rating_id'],
                                                                      'is_active': True})
    )
    await db.commit()

    ratings = await db.scalars(select(Rating).where(Rating.product_id == product.id,
                                                    Rating.is_active == True))
    rating_list = [rating.grade for rating in ratings.all()]
    if rating_list:
        await db.execute(
            update(Product).where(Product.id == product.id).values(rating=round(sum(rating_list) / len(rating_list), 1))
        )
    else:
        await db.execute(
            update(Product).where(Product.id == product.id).values(rating=0.0)
        )
    await db.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.delete('/{product_slug}')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str,
                         review_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete review"
        )

    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This product is not found"
        )

    review = await db.scalar(select(Review).where(Review.id == review_id, Review.is_active == True))

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This review is not found"
        )

    await db.execute(update(Review).where(Review.id == review_id).values(is_active=False))
    await db.execute(update(Rating).where(Rating.id == review.rating_id,
                                          ).values(is_active=False))

    await db.commit()

    ratings = await db.scalars(select(Rating).where(Rating.product_id == product.id,
                                                    Rating.is_active == True))
    rating_list = [rating.grade for rating in ratings.all()]
    if rating_list:
        await db.execute(
            update(Product).where(Product.id == product.id).values(rating=round(sum(rating_list) / len(rating_list), 1))
        )
    else:
        await db.execute(
            update(Product).where(Product.id == product.id).values(rating=0.0)
        )
    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Successful'
    }
