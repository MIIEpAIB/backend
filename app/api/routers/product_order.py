"""v1 商品订单：/api/product/order/*"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/product/order", tags=["ProductOrder"])

PAY_STATUS_CN = {"unpaid": "未付款", "paid": "已付款"}
SHIP_STATUS_CN = {"unshipped": "未发货", "shipped": "已发货", "received": "已收货"}


@router.get("/list", response_model=APIResponse[dict])
def order_list(
    order_no: str | None = Query(None),
    user_account: str | None = Query(None),
    product_name: str | None = Query(None),
    category_id: int | None = Query(None),
    pay_status: str | None = Query(None),
    ship_status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.ProductOrder).join(models.User, models.ProductOrder.user_id == models.User.id)
    if order_no:
        q = q.filter(models.ProductOrder.order_no == order_no)
    if user_account:
        q = q.filter(models.User.mobile.like(f"%{user_account}%"))
    if product_name:
        sub = db.query(models.ProductOrderItem.order_id).filter(models.ProductOrderItem.product_name.like(f"%{product_name}%"))
        q = q.filter(models.ProductOrder.id.in_(sub))
    if category_id:
        sub = db.query(models.ProductOrderItem.order_id).join(models.Product, models.ProductOrderItem.product_id == models.Product.id).filter(models.Product.category_id == category_id)
        q = q.filter(models.ProductOrder.id.in_(sub))
    if pay_status and pay_status != "all":
        if pay_status == "unpaid":
            q = q.filter(models.ProductOrder.pay_status == "unpaid")
        elif pay_status == "paid":
            q = q.filter(models.ProductOrder.pay_status == "paid")
    if ship_status and ship_status != "all":
        q = q.filter(models.ProductOrder.ship_status == ship_status)
    if start_date:
        try:
            q = q.filter(models.ProductOrder.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
        except ValueError:
            pass
    if end_date:
        try:
            q = q.filter(models.ProductOrder.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            pass
    total = q.count()
    rows = q.order_by(models.ProductOrder.id.desc()).offset((page_num - 1) * page_size).limit(page_size).all()
    list_ = []
    for o in rows:
        user = db.get(models.User, o.user_id)
        item = o.items[0] if o.items else None
        list_.append({
            "id": o.id,
            "order_no": o.order_no,
            "order_time": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "",
            "category_name": item.category_name if item else "",
            "product_name": item.product_name if item else "",
            "quantity": item.quantity if item else 0,
            "unit_price": float(item.price) if item else 0,
            "total_amount": float(o.amount_total),
            "user_account": user.mobile if user else "",
            "pay_status": PAY_STATUS_CN.get(o.pay_status, o.pay_status),
            "ship_status": SHIP_STATUS_CN.get(o.ship_status, o.ship_status),
            "express_company": o.express_company or "",
            "express_no": o.tracking_no or "",
        })
    return APIResponse[dict](code=0, msg="ok", data={"total": total, "list": list_})


@router.get("/detail", response_model=APIResponse[dict])
def order_detail(
    order_id: int | None = Query(None, alias="order_id"),
    order_no: str | None = Query(None, alias="order_no"),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    if order_id:
        o = db.get(models.ProductOrder, order_id)
    elif order_no:
        o = db.query(models.ProductOrder).filter(models.ProductOrder.order_no == order_no).first()
    else:
        raise HTTPException(400, "order_id 或 order_no 必填")
    if not o:
        raise HTTPException(404, "订单不存在")
    user = db.get(models.User, o.user_id)
    addr = db.get(models.UserAddress, o.address_id) if o.address_id else None
    item = o.items[0] if o.items else None
    data = {
        "order_no": o.order_no,
        "category_name": item.category_name if item else "",
        "user_account": user.mobile if user else "",
        "product_name": item.product_name if item else "",
        "quantity": item.quantity if item else 0,
        "total_amount": float(o.amount_total),
        "unit_price": float(item.price) if item else 0,
        "pay_status": PAY_STATUS_CN.get(o.pay_status, o.pay_status),
        "ship_status": SHIP_STATUS_CN.get(o.ship_status, o.ship_status),
        "order_time": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "",
        "ship_time": o.ship_time.strftime("%Y-%m-%d %H:%M:%S") if o.ship_time else "",
        "express_company": o.express_company or "",
        "express_no": o.tracking_no or "",
        "receive_time": o.receive_time.strftime("%Y-%m-%d %H:%M:%S") if o.receive_time else "",
        "receiver_name": addr.receiver_name if addr else "",
        "receiver_phone": addr.mobile if addr else "",
        "receiver_address": f"{addr.province or ''}{addr.city or ''}{addr.district or ''}{addr.detail_addr or ''}" if addr else "",
    }
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.get("/express-companies", response_model=APIResponse[dict])
def express_companies(admin: models.AdminUser = Depends(get_current_admin)):
    return APIResponse[dict](code=0, msg="ok", data={
        "list": ["顺丰", "申通", "韵达", "中通", "圆通", "邮政"]
    })


class ShipBody(BaseModel):
    order_id: int
    express_company: str
    express_no: str


@router.post("/ship", response_model=APIResponse[dict])
def ship(
    body: ShipBody,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    o = db.get(models.ProductOrder, body.order_id)
    if not o:
        raise HTTPException(404, "订单不存在")
    if o.pay_status != "paid":
        raise HTTPException(400, "仅已付款订单可发货")
    if o.ship_status != "unshipped":
        raise HTTPException(400, "订单已发货")
    from datetime import datetime
    o.express_company = body.express_company
    o.tracking_no = body.express_no
    o.ship_status = "shipped"
    o.ship_time = datetime.utcnow()
    db.commit()
    return APIResponse[dict](code=0, msg="发货成功", data=None)
