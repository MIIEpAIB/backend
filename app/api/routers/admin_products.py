from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse
from backend.app.schemas.product import (
    ProductCategoryOut,
    ProductCreate,
    ProductOut,
)


router = APIRouter(prefix="/api/admin", tags=["ProductAdmin"])


@router.get("/product-categories", response_model=APIResponse[list[ProductCategoryOut]])
def list_product_categories(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    cats = db.query(models.ProductCategory).order_by(models.ProductCategory.sort_order).all()
    return APIResponse[list[ProductCategoryOut]](
        code=0, msg="ok", data=[ProductCategoryOut.from_orm(c) for c in cats]
    )


@router.post("/product-categories", response_model=APIResponse[dict])
def create_product_category(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    cat = models.ProductCategory(name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return APIResponse[dict](code=0, msg="ok", data={"id": cat.id})


@router.get("/products", response_model=APIResponse[dict])
def list_products(
    name: str | None = Query(None),
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Product).join(models.ProductCategory)
    if name:
        q = q.filter(models.Product.name.like(f"%{name}%"))
    if category_id:
        q = q.filter(models.Product.category_id == category_id)
    total = q.count()
    rows = (
        q.order_by(models.Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result: list[ProductOut] = []
    for p in rows:
        zodiacs = p.zodiac_flags.split(",") if p.zodiac_flags else []
        result.append(
            ProductOut(
                id=p.id,
                name=p.name,
                category_id=p.category_id,
                category_name=p.category.name if p.category else None,
                price=float(p.price),
                stock=p.stock,
                zodiacs=zodiacs,
                is_home_show=bool(p.is_home_show),
                home_section=p.home_section,
                main_image=p.main_image,
            )
        )
    data = {"total": total, "list": [r.dict() for r in result]}
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.post("/products", response_model=APIResponse[dict])
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    cat = db.get(models.ProductCategory, payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="category not exists")
    zodiacs_str = ",".join(payload.zodiacs) if payload.zodiacs else None
    product = models.Product(
        name=payload.name,
        category_id=payload.category_id,
        price=payload.price,
        init_stock=payload.init_stock,
        stock=payload.init_stock,
        zodiac_flags=zodiacs_str,
        is_home_show=1 if payload.is_home_show else 0,
        home_section=payload.home_section,
        main_image=payload.main_image,
        description_html=payload.description_html,
        status=payload.status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return APIResponse[dict](code=0, msg="ok", data={"id": product.id})


@router.put("/products/{product_id}", response_model=APIResponse[dict])
def update_product(
    product_id: int,
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.name = payload.name
    product.category_id = payload.category_id
    product.price = payload.price
    product.init_stock = payload.init_stock
    product.stock = payload.init_stock  # 简化处理
    product.zodiac_flags = ",".join(payload.zodiacs) if payload.zodiacs else None
    product.is_home_show = 1 if payload.is_home_show else 0
    product.home_section = payload.home_section
    product.main_image = payload.main_image
    product.description_html = payload.description_html
    product.status = payload.status
    db.add(product)
    db.commit()
    return APIResponse[dict](code=0, msg="ok", data={"id": product.id})


@router.delete("/products/{product_id}", response_model=APIResponse[dict])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # 简化：直接删除；生产建议改为软删除
    db.delete(product)
    db.commit()
    return APIResponse[dict](code=0, msg="ok", data={})

