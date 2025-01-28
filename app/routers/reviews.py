from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.schemas import CreateReview
from app.models import User, Product
from .auth import get_current_user
from app.models.reviews import Review, Rating

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):

    pass


@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                           product_slug: str):
    pass


@router.post('/{product_slug}')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     product_slug: str,
                     review: CreateReview,
                     get_user: Annotated[dict, Depends(get_current_user)]):
    pass
#     if not get_user.get("is_customer"):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only customers can leave reviews"
#         )
#     product = await db.scalar(select(Product).where(Product.slug == product_slug,
#                                                     Product.is_active == True))
#     if not product:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="This product is not found"
#         )
#
#     await db.execute(insert(Review).values(user_id=get_user.get('id'),
#                                            product_id = product.id,
#                                            rating_id = review.rating_id,
#                                            comment = review.comment))
#     await db.execute(insert(Rating).values(grade=review.rating_id,
#                                            user_id=get_user.get('id'),
#                                            product_id=product.id))
#     await db.commit()
#     ratings = await db.scalars(select(Rating).where(Rating.product_id == product.id))
#     ratings = ratings.all()
#     await db.execute(update(Product).where(Product.id == product.id).values(rating=round(sum(ratings) / len(ratings), 1)))
#     await db.commit()
#
#     return {
#         'status_code': status.HTTP_201_CREATED,
#         'transaction': 'Successful'
#     }




@router.delete('/{product_slug}')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug):
    pass
