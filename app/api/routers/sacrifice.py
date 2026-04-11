"""v1 祭祀：贡品分类/列表、陵墓、订单、动态 /api/sacrifice/*"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/sacrifice", tags=["Sacrifice"])


# ---------- 贡品分类 ----------
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
    q = db.query(models.OfferingCategory)
    if category_name:
        q = q.filter(models.OfferingCategory.name.like(f"%{category_name}%"))
    if start_date:
        try:
            q = q.filter(models.OfferingCategory.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.OfferingCategory.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.OfferingCategory.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = [{"id": r.id, "category_name": r.name, "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""} for r in rows]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/category/all", response_model=APIResponse[dict])
def category_all(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    rows = db.query(models.OfferingCategory).order_by(models.OfferingCategory.id).all()
    list_ = [{"id": r.id, "category_name": r.name} for r in rows]
    return APIResponse[dict](code=0, msg="ok", data={"list": list_})


class CategoryAddBody(BaseModel):
    category_name: str


@router.post("/category/add", response_model=APIResponse[dict])
def category_add(
    body: CategoryAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    c = models.OfferingCategory(name=body.category_name)
    db.add(c)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


class CategoryEditBody(BaseModel):
    id: int
    category_name: str


@router.post("/category/edit", response_model=APIResponse[dict])
def category_edit(
    body: CategoryEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.query(models.OfferingCategory).filter(models.OfferingCategory.id == body.id).first()
    if not r:
        raise HTTPException(404, "分类不存在")
    r.name = body.category_name
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


# ---------- 贡品列表 ----------
@router.get("/tribute/list", response_model=APIResponse[dict])
def tribute_list(
    tribute_name: str | None = Query(None),
    category_id: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Offering)
    if tribute_name:
        q = q.filter(models.Offering.name.like(f"%{tribute_name}%"))
    if category_id:
        q = q.filter(models.Offering.category_id == category_id)
    if start_date:
        try:
            q = q.filter(models.Offering.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.Offering.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.Offering.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for r in rows:
        cat = db.get(models.OfferingCategory, r.category_id)
        list_.append({
            "id": r.id,
            "tribute_name": r.name,
            "category_id": r.category_id,
            "category_name": cat.name if cat else "",
            "image_url": r.icon or "",
            "price": r.price_coin,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class TributeAddBody(BaseModel):
    tribute_name: str
    category_id: int
    image_url: str = ""
    price: int


@router.post("/tribute/add", response_model=APIResponse[dict])
def tribute_add(
    body: TributeAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    o = models.Offering(name=body.tribute_name, category_id=body.category_id, price_coin=body.price, icon=body.image_url or None)
    db.add(o)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.post("/tribute/create", response_model=APIResponse[dict])
def tribute_create_alias(
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    """
    v1 文档使用 /api/sacrifice/tribute/create
    Body: { name, category_id, price, image_url }
    """
    tribute_name = body.get("tribute_name") or body.get("name") or ""
    category_id = body.get("category_id")
    price = body.get("price")
    image_url = body.get("image_url") or ""
    if not tribute_name or not category_id or price is None:
        raise HTTPException(status_code=400, detail="name/category_id/price required")
    o = models.Offering(name=tribute_name, category_id=category_id, price_coin=price, icon=image_url or None)
    db.add(o)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.get("/tribute/detail", response_model=APIResponse[dict])
def tribute_detail(
    id: int = Query(..., alias="id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Offering, id)
    if not r:
        raise HTTPException(404, "贡品不存在")
    return APIResponse[dict](code=0, msg="ok", data={"id": r.id, "tribute_name": r.name, "category_id": r.category_id, "image_url": r.icon or "", "price": r.price_coin})


class TributeEditBody(BaseModel):
    id: int
    tribute_name: str
    category_id: int
    image_url: str = ""
    price: int


@router.post("/tribute/edit", response_model=APIResponse[dict])
def tribute_edit(
    body: TributeEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.Offering, body.id)
    if not r:
        raise HTTPException(404, "贡品不存在")
    r.name = body.tribute_name
    r.category_id = body.category_id
    r.icon = body.image_url or None
    r.price_coin = body.price
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class TributeDeleteBody(BaseModel):
    id: int


@router.post("/tribute/delete", response_model=APIResponse[dict])
def tribute_delete(
    body: TributeDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.Offering).filter(models.Offering.id == body.id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# ---------- 祭祀动态 ----------
class SacrificeDynamicCreateBody(BaseModel):
    user_account: str
    tribute_name: str
    message: str
    deceased_name: str
    relationship: str


@router.post("/dynamic/create", response_model=APIResponse[dict])
def dynamic_create(
    body: SacrificeDynamicCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    feed = models.SacrificeFeed(
        user_mobile=body.user_account,
        offering_name=body.tribute_name,
        deceased_name=body.deceased_name,
        relation=body.relationship,
        content=body.message,
        sacrifice_time=datetime.utcnow(),
        created_by_admin=admin.id,
    )
    db.add(feed)
    db.commit()
    return APIResponse[dict](code=0, msg="创建成功", data=None)


@router.get("/dynamic/list", response_model=APIResponse[dict])
def dynamic_list(
    user_account: str | None = Query(None),
    tribute_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.SacrificeFeed)
    if user_account:
        q = q.filter(models.SacrificeFeed.user_mobile.like(f"%{user_account}%"))
    if tribute_name:
        q = q.filter(models.SacrificeFeed.offering_name.like(f"%{tribute_name}%"))
    if start_date:
        try:
            q = q.filter(models.SacrificeFeed.sacrifice_time >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.SacrificeFeed.sacrifice_time
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.SacrificeFeed.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = []
    for r in rows:
        list_.append(
            {
                "id": r.id,
                "user_account": r.user_mobile or "",
                "tribute_name": r.offering_name or "",
                "deceased_name": r.deceased_name or "",
                "relationship": r.relation or "",
                "message": r.content or "",
                "created_at": r.sacrifice_time.strftime("%Y-%m-%d %H:%M:%S") if r.sacrifice_time else "",
            }
        )
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


# ---------- 网上陵园 ----------
@router.get("/cemetery/list", response_model=APIResponse[dict])
def cemetery_list(
    user_account: str | None = Query(None),
    deceased_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.Cemetery)
    if user_account:
        q = q.filter(models.Cemetery.creator_account.like(f"%{user_account}%"))
    if deceased_name:
        q = q.filter(models.Cemetery.deceased_name.like(f"%{deceased_name}%"))
    if start_date:
        try:
            q = q.filter(models.Cemetery.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.Cemetery.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(models.Cemetery.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )
    list_ = []
    for r in rows:
        list_.append(
            {
                "id": r.id,
                "user_account": r.creator_account or "",
                "deceased_name": r.deceased_name,
                "relationship": r.relation or "",
                "gender": "男" if r.gender in ("male", "男") else "女",
                "birth_date": r.birthday.isoformat() if r.birthday else "",
                "death_date": r.death_day.isoformat() if r.death_day else "",
                "epitaph": r.epitaph or "",
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            }
        )
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class CemeteryCreateBody(BaseModel):
    user_account: str
    deceased_name: str
    gender: str
    birth_date: str | None = None
    death_date: str | None = None
    relationship: str = ""
    image_url: str = ""
    epitaph: str = ""


@router.post("/cemetery/create", response_model=APIResponse[dict])
def cemetery_create(
    body: CemeteryCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    from datetime import date as _date

    gender = "male" if body.gender in ("男", "male", "m") else "female"
    birthday = None
    death_day = None
    if body.birth_date:
        try:
            birthday = datetime.strptime(body.birth_date, "%Y-%m-%d").date()
        except ValueError:
            birthday = None
    if body.death_date:
        try:
            death_day = datetime.strptime(body.death_date, "%Y-%m-%d").date()
        except ValueError:
            death_day = None
    c = models.Cemetery(
        creator_account=body.user_account,
        deceased_name=body.deceased_name,
        gender=gender,
        birthday=birthday,
        death_day=death_day,
        relation=body.relationship,
        avatar_url=body.image_url or None,
        epitaph=body.epitaph or None,
    )
    db.add(c)
    db.commit()
    return APIResponse[dict](code=0, msg="创建成功", data=None)


# ---------- 祭祀消费订单 ----------
@router.get("/order/list", response_model=APIResponse[dict])
def sacrifice_order_list(
    user_account: str | None = Query(None),
    tribute_name: str | None = Query(None),
    category_id: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.SacrificeOrder)

    if tribute_name:
        q = q.filter(models.SacrificeOrder.offering_name.like(f"%{tribute_name}%"))

    if start_date:
        try:
            q = q.filter(models.SacrificeOrder.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(
                models.SacrificeOrder.created_at
                <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            )
        except ValueError:
            pass

    if user_account:
        user_ids = (
            db.query(models.User.id)
            .filter(models.User.mobile.like(f"%{user_account}%"))
            .subquery()
        )
        q = q.filter(models.SacrificeOrder.user_id.in_(user_ids))

    if category_id:
        offering_ids = (
            db.query(models.Offering.id)
            .filter(models.Offering.category_id == category_id)
            .subquery()
        )
        q = q.filter(models.SacrificeOrder.offering_id.in_(offering_ids))

    total = q.count()
    rows = (
        q.order_by(models.SacrificeOrder.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    list_ = []
    for r in rows:
        u = db.get(models.User, r.user_id)
        offering = db.get(models.Offering, r.offering_id)
        cat = db.get(models.OfferingCategory, offering.category_id) if offering else None
        list_.append(
            {
                "id": r.id,
                "user_account": u.mobile if u else "",
                "tribute_name": r.offering_name or "",
                "category_name": (cat.name if cat else (r.offering_category or "")),
                "deceased_name": r.deceased_name or "",
                "unit_price": int(r.price_coin or 0),
                "quantity": int(r.quantity or 0),
                "total_price": int(r.total_coin or 0),
                "rmb_equivalent": float(r.rmb_amount) if r.rmb_amount is not None else 0.0,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            }
        )

    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})
