from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, Rating


async def update_rating(db: AsyncSession,
                        product_id: int):
    '''корутина пересчитывает рейтинг товара в базе данных <db> по его id <product_id>'''

    ratings = await db.scalars(select(Rating).where(Rating.product_id == product_id,
                                                    Rating.is_active == True))
    rating_list = [rating.grade for rating in ratings.all()]
    if rating_list:
        await db.execute(
            update(Product).where(Product.id == product_id).values(rating=round(sum(rating_list) / len(rating_list), 1))
        )
    else:
        await db.execute(
            update(Product).where(Product.id == product_id).values(rating=0.0)
        )
    await db.commit()


async def get_object_or_404(db: AsyncSession, model, expression: tuple):
    obj = await db.scalar(select(model).where(*expression))
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Object is not found"
        )
    return obj


async def get_objects_or_404(db: AsyncSession, model, expression: tuple):
    objects_set = await db.scalars(select(model).where(*expression))
    objects = objects_set.all()
    if objects:
        return objects

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{model.__tablename__.capitalize()} are not found"
    )
