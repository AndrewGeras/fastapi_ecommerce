from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.models import *
from app.routers.auth import get_current_user

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active == True,
                                                      Product.stock > 0))
    if products:
        return products.all()

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="There are no product"
    )


@router.post('/')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)],
                         create_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin") and not get_user.get("is_supplier"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )

    category = await db.scalar(select(Category).where(Category.id == create_product.category))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    await db.execute(insert(Product).values(name=create_product.name,
                                            description=create_product.description,
                                            price=create_product.price,
                                            image_url=create_product.image_url,
                                            stock=create_product.stock,
                                            category_id=create_product.category,
                                            # rating=0.0,
                                            slug=slugify(create_product.name),
                                            supplier_id=get_user.get("id")))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)],
                              category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))
    cat_ids = [category.id] + [cat.id for cat in subcategories.all()]

    products = await db.scalars(select(Product).where(Product.category_id.in_(cat_ids),
                                                      Product.is_active == True,
                                                      Product.stock > 0
                                                      ))
    if products:
        return products.all()
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="There are no active product on stock"
    )


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.is_active == True,
                                                    Product.stock > 0))
    if product:
        return product

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="There are no product"
    )


@router.put('/{product_slug}')
async def update_product(db: Annotated[AsyncSession, Depends(get_db)],
                         upd_product: CreateProduct,
                         product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin") and not get_user.get("is_supplier"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )

    product = await db.scalar(select(Product).where(Product.slug == product_slug,
                                                    Product.supplier_id == get_user.get("id", 0)))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    category = await db.scalar(select(Category).where(Category.id == upd_product.category))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no category found'
        )
    await db.execute(update(Product).where(Product.slug == product_slug).values(name=upd_product.name,
                                                                                slug=slugify(upd_product.name),
                                                                                description=upd_product.description,
                                                                                price=upd_product.price,
                                                                                image_url=upd_product.image_url,
                                                                                stock=upd_product.stock,
                                                                                rating=0.0,
                                                                                category_id=upd_product.category))
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }



@router.delete('/')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)],
                         product_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin") and not get_user.get("is_supplier"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )

    product = await db.scalar(select(Product).where(Product.id == product_id,
                                                    Product.supplier_id == get_user.get("id", 0)))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }
