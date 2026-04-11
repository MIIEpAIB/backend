"""v1 祈福：物件、订单、动态 /api/blessing/*"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/blessing", tags=["Blessing"])


# ---------- 祈福物件 ----------
@router.get("/item/list", response_model=APIResponse[dict])
def item_list(
    item_name: str | None = Query(None),
    min_price: int | None = Query(None),
    max_price: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.BlessItem)
    if item_name:
        q = q.filter(models.BlessItem.name.like(f"%{item_name}%"))
    if min_price is not None:
        q = q.filter(models.BlessItem.price_coin >= min_price)
    if max_price is not None:
        q = q.filter(models.BlessItem.price_coin <= max_price)
    if start_date:
        try:
            q = q.filter(models.BlessItem.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.BlessItem.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.BlessItem.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for r in rows:
        list_.append({
            "id": r.id,
            "item_name": r.name,
            "image_url": getattr(r, "icon", "") or getattr(r, "image_url", "") or "",
            "price": r.price_coin,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/item/all", response_model=APIResponse[dict])
def item_all(
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    rows = db.query(models.BlessItem).filter(models.BlessItem.status == "on").order_by(models.BlessItem.id).all()
    list_ = [{"id": r.id, "item_name": r.name} for r in rows]
    return APIResponse[dict](code=0, msg="ok", data={"list": list_})


class ItemAddBody(BaseModel):
    item_name: str
    image_url: str = ""
    price: int


@router.post("/item/add", response_model=APIResponse[dict])
def item_add(
    body: ItemAddBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    item = models.BlessItem(name=body.item_name, price_coin=body.price)
    db.add(item)
    db.commit()
    return APIResponse[dict](code=0, msg="新增成功", data=None)


@router.get("/item/detail", response_model=APIResponse[dict])
def item_detail(
    id: int = Query(..., alias="id"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.BlessItem, id)
    if not r:
        raise HTTPException(404, "祈福物件不存在")
    return APIResponse[dict](code=0, msg="ok", data={
        "id": r.id,
        "item_name": r.name,
        "image_url": getattr(r, "icon", "") or getattr(r, "image_url", "") or "",
        "price": r.price_coin,
    })


class ItemEditBody(BaseModel):
    id: int
    item_name: str
    image_url: str = ""
    price: int


@router.post("/item/edit", response_model=APIResponse[dict])
def item_edit(
    body: ItemEditBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    r = db.get(models.BlessItem, body.id)
    if not r:
        raise HTTPException(404, "祈福物件不存在")
    r.name = body.item_name
    r.price_coin = body.price
    db.commit()
    return APIResponse[dict](code=0, msg="保存成功", data=None)


class ItemDeleteBody(BaseModel):
    id: int


@router.post("/item/delete", response_model=APIResponse[dict])
def item_delete(
    body: ItemDeleteBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    db.query(models.BlessItem).filter(models.BlessItem.id == body.id).delete()
    db.commit()
    return APIResponse[dict](code=0, msg="删除成功", data=None)


# ---------- 祈福动态 ----------
@router.get("/dynamic/list", response_model=APIResponse[dict])
def dynamic_list(
    user_account: str | None = Query(None),
    item_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.BlessFeed)
    if user_account:
        q = q.filter(models.BlessFeed.display_name.like(f"%{user_account}%"))
    if item_name:
        q = q.filter(models.BlessFeed.bless_item_name.like(f"%{item_name}%"))
    if start_date:
        try:
            q = q.filter(models.BlessFeed.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.BlessFeed.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.BlessFeed.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = [{
        "id": r.id,
        "user_account": r.display_name,
        "item_name": r.bless_item_name or "",
        "blessing_message": r.content,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
    } for r in rows]
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


class DynamicCreateBody(BaseModel):
    user_account: str
    item_id: int | None = None
    item_name: str | None = None
    blessing_message: str


@router.post("/dynamic/create", response_model=APIResponse[dict])
def dynamic_create(
    body: DynamicCreateBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    item_name = body.item_name or ""
    if body.item_id:
        item = db.get(models.BlessItem, body.item_id)
        if item:
            item_name = item.name
    feed = models.BlessFeed(
        display_name=body.user_account,
        bless_item_id=body.item_id,
        bless_item_name=item_name or None,
        content=body.blessing_message,
        created_by_admin=admin.id,
    )
    db.add(feed)
    db.commit()
    return APIResponse[dict](code=0, msg="创建成功", data=None)


# ---------- 祈福消费订单 ----------
@router.get("/order/list", response_model=APIResponse[dict])
def order_list(
    user_account: str | None = Query(None),
    item_name: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.BlessOrder).join(models.User, models.BlessOrder.user_id == models.User.id)
    if user_account:
        q = q.filter(models.User.mobile.like(f"%{user_account}%"))
    if item_name:
        q = q.filter(models.BlessOrder.item_name.like(f"%{item_name}%"))
    if start_date:
        try:
            q = q.filter(models.BlessOrder.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.BlessOrder.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.BlessOrder.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for r in rows:
        user = db.get(models.User, r.user_id)
        list_.append({
            "id": r.id,
            "user_account": user.mobile if user else "",
            "item_name": r.item_name,
            "item_price": r.price_coin,
            "quantity": r.quantity,
            "total_price": r.total_coin,
            "rmb_amount": float(r.rmb_amount),
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})
