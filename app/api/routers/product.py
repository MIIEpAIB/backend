"""v1 商品与分类：/api/product/category/* 与 /api/product/*"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/product", tags=["Product"])


# ---------- 商品分类 ----------
@router.get("/category/list", response_model=APIResponse[dict])
def category_list(
    category_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.ProductCategory)
    if category_name:
        q = q.filter(models.ProductCategory.name.like(f"%{category_name}%"))
    if start_date:
        try:
            q = q.filter(models.ProductCategory.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.ProductCategory.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.ProductCategory.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = [{"id": r.id, "category_name": r.name, "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""} for r in rows]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class CategoryAddBody(BaseModel):
    category_name: str


@router.post("/category/add", response_model=APIResponse[dict])
def category_add(
    body: CategoryAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    c = models.ProductCategory(name=body.category_name)
    db.add(c)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.get("/category/detail", response_model=APIResponse[dict])
def category_detail(
    id: int = Query(..., alias="id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.query(models.ProductCategory).filter(models.ProductCategory.id == id).first()
    if not r:
        raise HTTPException(404, "分类不存在")
    return APIResponse[dict](code=0, msg="ok", data={"id": r.id, "category_name": r.name})


class CategoryEditBody(BaseModel):
    id: int
    category_name: str


@router.post("/category/edit", response_model=APIResponse[dict])
def category_edit(
    body: CategoryEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.query(models.ProductCategory).filter(models.ProductCategory.id == body.id).first()
    if not r:
        raise HTTPException(404, "分类不存在")
    r.name = body.category_name
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class CategoryDeleteBody(BaseModel):
    id: int


@router.post("/category/delete", response_model=APIResponse[dict])
def category_delete(
    body: CategoryDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    exists = db.query(models.Product).filter(models.Product.category_id == body.id).first()
    if exists:
        return APIResponse[dict](code=400, msg="该分类下存在商品，无法删除", data=None)
    db.query(models.ProductCategory).filter(models.ProductCategory.id == body.id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# ---------- 商品列表 ----------
@router.get("/list", response_model=APIResponse[dict])
def product_list(
    product_name: str | None = Query(None),
    category_id: int | None = Query(None),
    zodiac: str | None = Query(None),
    is_home_display: int | None = Query(None),
    home_category: str | None = Query(None),
    stock_filter: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Product).join(models.ProductCategory, models.Product.category_id == models.ProductCategory.id)
    if product_name:
        q = q.filter(models.Product.name.like(f"%{product_name}%"))
    if category_id:
        q = q.filter(models.Product.category_id == category_id)
    if zodiac:
        q = q.filter(models.Product.zodiac_flags.like(f"%{zodiac}%"))
    if is_home_display is not None:
        q = q.filter(models.Product.is_home_show == is_home_display)
    if home_category:
        q = q.filter(models.Product.home_section == home_category)
    if stock_filter == "gt10":
        q = q.filter(models.Product.stock > 10)
    elif stock_filter == "lt10":
        q = q.filter(models.Product.stock < 10)
    if start_date:
        try:
            q = q.filter(models.Product.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.Product.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.Product.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for p in rows:
        cat = p.category if hasattr(p, "category") and p.category else None
        zodiac_str = (p.zodiac_flags or "").replace(",", "，") or ""
        sold = (p.init_stock or 0) - (p.stock or 0)
        list_.append({
            "id": p.id,
            "product_name": p.name,
            "category_name": cat.name if cat else "",
            "price": float(p.price),
            "zodiac": zodiac_str,
            "is_home_display": 1 if p.is_home_show else 0,
            "home_category": p.home_section or "",
            "total_stock": p.init_stock or 0,
            "sold_stock": max(0, sold),
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class ProductAddBody(BaseModel):
    product_name: str
    category_id: int
    price: float
    zodiac: list[str] = []
    initial_stock: int = 0
    is_home_display: int = 0
    home_category: str = ""
    main_image: str = ""
    detail_images: list[str] = []
    blessing_images: list[str] = []
    description: str = ""


@router.post("/add", response_model=APIResponse[dict])
def product_add(
    body: ProductAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    if not db.get(models.ProductCategory, body.category_id):
        raise HTTPException(400, "分类不存在")
    zodiac_str = ",".join(body.zodiac) if body.zodiac else None
    p = models.Product(
        name=body.product_name,
        category_id=body.category_id,
        price=body.price,
        init_stock=body.initial_stock,
        stock=body.initial_stock,
        zodiac_flags=zodiac_str,
        is_home_show=body.is_home_display,
        home_section=body.home_category or None,
        main_image=body.main_image or None,
        description_html=body.description or None,
    )
    db.add(p)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.get("/detail", response_model=APIResponse[dict])
def product_detail(
    id: int = Query(..., alias="id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    p = db.get(models.Product, id)
    if not p:
        raise HTTPException(404, "商品不存在")
    zodiac_list = (p.zodiac_flags or "").split(",") if p.zodiac_flags else []
    return APIResponse[dict](code=0, msg="ok", data={
        "id": p.id,
        "product_name": p.name,
        "category_id": p.category_id,
        "price": float(p.price),
        "zodiac": zodiac_list,
        "initial_stock": p.init_stock or 0,
        "is_home_display": 1 if p.is_home_show else 0,
        "home_category": p.home_section or "",
        "main_image": p.main_image or "",
        "detail_images": [],
        "blessing_images": [],
        "description": p.description_html or "",
    })


class ProductEditBody(BaseModel):
    id: int
    product_name: str
    category_id: int
    price: float
    zodiac: list[str] = []
    initial_stock: int = 0
    is_home_display: int = 0
    home_category: str = ""
    main_image: str = ""
    detail_images: list[str] = []
    blessing_images: list[str] = []
    description: str = ""


@router.post("/edit", response_model=APIResponse[dict])
def product_edit(
    body: ProductEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    p = db.get(models.Product, body.id)
    if not p:
        raise HTTPException(404, "商品不存在")
    p.name = body.product_name
    p.category_id = body.category_id
    p.price = body.price
    p.init_stock = body.initial_stock
    p.stock = body.initial_stock
    p.zodiac_flags = ",".join(body.zodiac) if body.zodiac else None
    p.is_home_show = body.is_home_display
    p.home_section = body.home_category or None
    p.main_image = body.main_image or None
    p.description_html = body.description or None
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class ProductDeleteBody(BaseModel):
    id: int


@router.post("/delete", response_model=APIResponse[dict])
def product_delete(
    body: ProductDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    p = db.get(models.Product, body.id)
    if not p:
        raise HTTPException(404, "商品不存在")
    db.delete(p)
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)
