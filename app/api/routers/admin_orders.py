from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_admin
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse
from backend.app.schemas.product import ProductOrderItemOut, ProductOrderOut


router = APIRouter(prefix="/api/admin/orders", tags=["ProductOrderAdmin"])


@router.get("/products", response_model=APIResponse[dict])
def list_product_orders(
    order_no: str | None = Query(None),
    user_mobile: str | None = Query(None),
    pay_status: str | None = Query(None),
    ship_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    q = db.query(models.ProductOrder).join(models.User)
    if order_no:
        q = q.filter(models.ProductOrder.order_no == order_no)
    if user_mobile:
        q = q.filter(models.User.mobile.like(f"%{user_mobile}%"))
    if pay_status in ("unpaid", "paid"):
        q = q.filter(models.ProductOrder.pay_status == pay_status)
    if ship_status in ("unshipped", "shipped", "received"):
        q = q.filter(models.ProductOrder.ship_status == ship_status)

    total = q.count()
    rows = (
        q.order_by(models.ProductOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    data_list: list[ProductOrderOut] = []
    for o in rows:
        items = [
            ProductOrderItemOut(
                product_id=i.product_id,
                product_name=i.product_name,
                price=float(i.price),
                quantity=i.quantity,
                amount=float(i.amount),
            )
            for i in o.items
        ]
        data_list.append(
            ProductOrderOut(
                id=o.id,
                order_no=o.order_no,
                user_id=o.user_id,
                user_mobile=o.user.mobile if o.user else "",
                amount_total=float(o.amount_total),
                pay_status=o.pay_status,
                ship_status=o.ship_status,
                express_company=o.express_company,
                tracking_no=o.tracking_no,
                created_at=o.created_at,
                items=items,
            )
        )

    data = {"total": total, "list": [d.dict() for d in data_list]}
    return APIResponse[dict](code=0, msg="ok", data=data)


@router.post("/products/{order_id}/ship", response_model=APIResponse[dict])
def ship_product_order(
    order_id: int,
    body: dict,
    db: Session = Depends(get_db),
    admin: models.AdminUser = Depends(get_current_admin),
):
    express_company = body.get("express_company")
    tracking_no = body.get("tracking_no")
    if not express_company or not tracking_no:
        raise HTTPException(status_code=400, detail="express_company and tracking_no required")

    order = db.get(models.ProductOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.pay_status != "paid":
        raise HTTPException(status_code=400, detail="Order not paid")
    if order.ship_status != "unshipped":
        raise HTTPException(status_code=400, detail="Order already shipped")

    order.express_company = express_company
    order.tracking_no = tracking_no
    order.ship_status = "shipped"
    db.add(order)
    db.commit()
    return APIResponse[dict](code=0, msg="ok", data={"id": order.id})

