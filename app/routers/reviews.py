from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


from app.backend.db_depends import get_db
from app.schemas import CreateReview
from app.models import User, Product, Review, Rating
from .auth import get_current_user
from app.services.service import update_rating, get_object_or_404, get_objects_or_404

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await get_objects_or_404(db, Review, (Review.is_active == True,))

    #  Получаем список всех отзывов со связвнными с ними объектами товаров, пользователей и рейтингов
    objects = [
        {'review': review,
         'product': await get_object_or_404(db, Product, (Product.id == review.product_id,)),
         'user': await get_object_or_404(db, User, (User.id == review.user_id,)),
         'rating': await get_object_or_404(db, Rating, (Rating.id == review.rating_id,))}
        for review in reviews]

    return [{'product_slug': obj['product'].slug,
             'user': obj['user'].username,
             'comment_date': obj['review'].comment_date,
             'comment': obj['review'].comment,
             'rating': obj['rating'].grade} for obj in objects]



@router.get('/{product_slug}')
async def products_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                           product_slug: str):
    product = await get_object_or_404(db, Product, (Product.slug == product_slug, Product.is_active == True))
    reviews = await get_objects_or_404(db, Review, (Review.product_id == product.id, Review.is_active == True))

    #  Получаем список отзывов по товару со связвнными с ними объектами пользователей и рейтингов
    objects = [
        {'review': review,
         'user': await get_object_or_404(db, User, (User.id == review.user_id,)),
         'rating': await get_object_or_404(db, Rating, (Rating.id == review.rating_id,))}
        for review in reviews]

    return [{'user': obj['user'].username,
             'comment_date': obj['review'].comment_date,
             'comment': obj['review'].comment,
             'rating': obj['rating'].grade} for obj in objects]


@router.post('/{product_slug}')
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                     product_slug: str,
                     review: CreateReview,
                     get_user: Annotated[dict, Depends(get_current_user)]):
    #  проверяем является ли пользователь покупателем
    if not get_user.get("is_customer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can leave reviews"
        )

    #  получаем из базы данных объект товара по слагу
    product = await get_object_or_404(db, Product, (Product.slug == product_slug, Product.is_active == True))

    #  значения полей нового рейтинга для занесения в БД
    new_rating = {'grade': review.rating_grade,
                  'user_id': get_user.get('id'),
                  'product_id': product.id}

    #  Запись с рейтингом либо заносится впервые, либо обновляется при наличии в БД и при совпадении пользователя и товара
    await db.execute(
        insert(Rating).values(new_rating).on_conflict_do_update(constraint='uc_rating_user_product',
                                                                set_={'grade': new_rating['grade'],
                                                                      'is_active': True}))
    await db.commit()

    #  Получаем объект рейтинга из БД
    rating = await get_object_or_404(db, Rating,
                                     (Rating.user_id == get_user.get('id'), Rating.product_id == product.id))

    #  значения полей нового отзыва для занесения в БД
    new_review = {'comment': review.comment,
                  'user_id': get_user.get('id'),
                  'product_id': product.id,
                  'rating_id': rating.id}

    #  Запись с отзывом либо заносится впервые, либо обновляется при наличии в БД и при совпадении пользователя и товара
    await db.execute(
        insert(Review).values(new_review).on_conflict_do_update(constraint='uc_review_user_product',
                                                                set_={'comment': new_review['comment'],
                                                                      'rating_id': new_review['rating_id'],
                                                                      'comment_date': datetime.now(),
                                                                      'is_active': True})
    )
    await db.commit()

    #  обновляем рейтинг товара в БД
    await update_rating(db, product.id)

    #  возвращаем сообщение об успешном размещении отзыва
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.delete('/{product_slug}')
async def delete_reviews(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str,
                         review_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    #  проверяем является ли пользователь администратором
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete review"
        )

    #  получаем из базы данных объект товара по слагу
    product = await get_object_or_404(db, Product, (Product.slug == product_slug, Product.is_active == True))

    #  получаем из базы данных объект отзыва по идентификатору
    review = await get_object_or_404(db, Review, (Review.id == review_id, Review.is_active == True))

    #  деактивируем отзыв и соответствующую отметку рейтинга
    await db.execute(update(Review).where(Review.id == review_id).values(is_active=False))
    await db.execute(update(Rating).where(Rating.id == review.rating_id).values(is_active=False))
    await db.commit()

    #  обновляем рейтинг товара в БД
    await update_rating(db, product.id)

    #  возвращаем сообщение об успешном удалении отзыва
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Successful'
    }
