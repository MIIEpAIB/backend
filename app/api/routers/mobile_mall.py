"""移动端接口 v1：商城 /api/mall/*, /api/account/recharge/*"""

from datetime import datetime
from decimal import Decimal
import random

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.mobile_deps import mobile_user_id_from_header
from backend.app.db import models
from backend.app.db.database import get_db
from backend.app.schemas.common import APIResponse

router_mall = APIRouter(prefix="/api/mall", tags=["Mobile-Mall"])
router_account = APIRouter(prefix="/api/account", tags=["Mobile-Account"])

# 文档枚举（用于返回 type_name / zodiac_name，若找不到则回退为空）
_TYPE_MAP = {
    "fortune": "财运",
    "safety": "保平安",
    "health": "健康",
    "transshipment": "转运",
    "town_house": "镇宅",
    "study": "学习",
    "zodiac": "本命",
    "love": "爱情",
    "business": "生意",
}

_ZODIAC_MAP = {
    "rat": "鼠",
    "ox": "牛",
    "tiger": "虎",
    "rabbit": "兔",
    "dragon": "龙",
    "snake": "蛇",
    "horse": "马",
    "goat": "羊",
    "monkey": "猴",
    "rooster": "鸡",
    "dog": "狗",
    "pig": "猪",
}


def _infer_type_and_zodiac_from_flags(flags: str | None) -> tuple[str, str]:
    """从 product.zodiac_flags 推断 type_name / zodiac_name（尽量贴近文档）。"""
    tokens = [t.strip() for t in (flags or "").split(",") if t.strip()]
    type_name = ""
    zodiac_name = ""
    for t in tokens:
        if not type_name and t in _TYPE_MAP:
            type_name = _TYPE_MAP[t]
        if not zodiac_name and t in _ZODIAC_MAP:
            zodiac_name = _ZODIAC_MAP[t]
    return type_name, zodiac_name


@router_mall.get("/product/filter/options", response_model=APIResponse[dict])
def mobile_mall_filter_options():
    """移动端：商品筛选选项（分类、生肖、价格等）"""
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "type_list": [{"type_code": k, "type_name": v} for k, v in _TYPE_MAP.items()],
            "zodiac_list": [{"zodiac_code": k, "zodiac_name": v} for k, v in _ZODIAC_MAP.items()],
            # 前端目前未使用该字段，但按文档保留
            "price_ranges": [],
        },
    )


@router_mall.get("/product/list", response_model=APIResponse[dict])
def mobile_mall_product_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    type_code: str | None = Query(None),
    zodiac_code: str | None = Query(None),
    price_min: int | None = Query(None),
    price_max: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """移动端：商品列表"""
    q = (
        db.query(models.Product)
        .join(models.ProductCategory, models.Product.category_id == models.ProductCategory.id)
        .filter(models.Product.status == "on")
    )

    # type/zodiac/price 过滤：利用 product.zodiac_flags 字段做模糊匹配（product 表里这个字段是逗号分隔的）
    if type_code:
        q = q.filter(models.Product.zodiac_flags.like(f"%{type_code}%"))
    if zodiac_code:
        q = q.filter(models.Product.zodiac_flags.like(f"%{zodiac_code}%"))
    if price_min is not None:
        q = q.filter(models.Product.price >= price_min)
    if price_max is not None:
        q = q.filter(models.Product.price <= price_max)

    total = q.count()
    rows = (
        q.order_by(models.Product.id.desc())
        .offset((page_num - 1) * page_size)
        .limit(page_size)
        .all()
    )

    list_ = []
    for p in rows:
        type_name, zodiac_name = _infer_type_and_zodiac_from_flags(p.zodiac_flags)
        sold = max(0, (p.init_stock or 0) - (p.stock or 0))

        list_.append(
            {
                # 文档字段
                "product_id": str(p.id),
                "product_name": p.name,
                "product_image": p.main_image or "",
                "price": float(p.price),
                "type_name": type_name or "",
                "zodiac_name": zodiac_name or "",
                # 前端页面字段兼容
                "icon": p.main_image or "",
                "description": p.description_html or "",
                "content": p.description_html or "",
                "sales": sold,
            }
        )

    return APIResponse(code=0, msg="ok", data={"total": total, "page_num": page_num, "page_size": page_size, "list": list_})

@router_mall.get("/product/detail", response_model=APIResponse[dict])
def mobile_mall_product_detail(
    product_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """移动端：商品详情"""
    try:
        pid = int(product_id)
    except ValueError:
        pid = 0

    p = db.get(models.Product, pid) if pid else None
    if not p:
        return APIResponse(code=0, msg="ok", data={"product_id": product_id, "product_name": "", "price": 0, "description": "", "stock": 0, "product_images": []})

    type_name, zodiac_name = _infer_type_and_zodiac_from_flags(p.zodiac_flags)
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "product_id": str(p.id),
            "product_name": p.name,
            "product_images": [p.main_image or ""],
            "price": float(p.price),
            "type_name": type_name or "",
            "zodiac_name": zodiac_name or "",
            "description": p.description_html or "",
            "content": p.description_html or "",
            "stock": p.stock or 0,
            # 前端字段
            "icon": p.main_image or "",
            "sales": max(0, (p.init_stock or 0) - (p.stock or 0)),
        },
    )


class MallCartAddBody(BaseModel):
    product_id: str = ""
    quantity: int = 1


@router_mall.post("/cart/add", response_model=APIResponse[dict])
def mobile_mall_cart_add(body: MallCartAddBody):
    """移动端：加入购物车"""
    return APIResponse(code=0, msg="ok", data={"cart_id": "uuid", "message": "加入购物车成功"})


class MallOrderLine(BaseModel):
    product_id: str = ""
    quantity: int = 1


class MallOrderCreateBody(BaseModel):
    address_id: str = ""
    pay_method: str = "balance"
    items: list[MallOrderLine] | None = None
    product_id: str = ""
    quantity: int = 1


def _gen_order_no() -> str:
    return "M" + datetime.utcnow().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))


@router_mall.post("/order/create", response_model=APIResponse[dict])
def mobile_mall_order_create(
    body: MallOrderCreateBody,
    db: Session = Depends(get_db),
    user_id: int = Depends(mobile_user_id_from_header),
):
    """移动端：创建实物商品订单（待支付）。"""
    lines = list(body.items or [])
    if not lines:
        lines = [MallOrderLine(product_id=body.product_id, quantity=body.quantity)]
    lines = [ln for ln in lines if (ln.product_id or "").strip() and int(ln.quantity or 0) > 0]
    if not lines:
        raise HTTPException(status_code=400, detail="请选择商品")

    try:
        aid = int(body.address_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="请选择收货地址")
    addr = db.get(models.UserAddress, aid)
    if not addr or int(addr.user_id) != int(user_id):
        raise HTTPException(status_code=400, detail="收货地址无效")

    pm = (body.pay_method or "balance").lower()
    if pm not in ("balance", "wechat", "alipay"):
        pm = "balance"

    amount_product = Decimal("0")
    order_lines: list[tuple[models.Product, int, Decimal]] = []
    for ln in lines:
        try:
            pid = int(ln.product_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"商品不存在：{ln.product_id}")
        p = db.get(models.Product, pid)
        if not p or p.status != "on":
            raise HTTPException(status_code=400, detail="商品已下架或不存在")
        qty = int(ln.quantity)
        if qty < 1:
            raise HTTPException(status_code=400, detail="购买数量无效")
        if int(p.stock or 0) < qty:
            raise HTTPException(status_code=400, detail=f"库存不足：{p.name}")
        line_price = Decimal(str(p.price))
        amount_product += line_price * qty
        order_lines.append((p, qty, line_price))

    amount_shipping = Decimal("0")
    amount_total = amount_product + amount_shipping

    order_no = _gen_order_no()
    while db.query(models.ProductOrder).filter(models.ProductOrder.order_no == order_no).first():
        order_no = _gen_order_no()

    order = models.ProductOrder(
        order_no=order_no,
        user_id=user_id,
        address_id=aid,
        amount_product=amount_product,
        amount_shipping=amount_shipping,
        amount_total=amount_total,
        pay_status="unpaid",
        ship_status="unshipped",
        pay_method=pm,
    )
    db.add(order)
    db.flush()

    cat_name_cache: dict[int, str] = {}
    for p, qty, line_price in order_lines:
        cid = int(p.category_id)
        if cid not in cat_name_cache:
            c = db.get(models.ProductCategory, cid)
            cat_name_cache[cid] = c.name if c else ""
        line_total = line_price * qty
        db.add(
            models.ProductOrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name=p.name,
                category_name=cat_name_cache[cid],
                price=line_price,
                quantity=qty,
                amount=line_total,
            )
        )

    db.commit()
    db.refresh(order)
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "order_id": str(order.id),
            "order_no": order.order_no,
            "total_amount": float(order.amount_total),
            "pay_status": order.pay_status,
            "pay_method": order.pay_method,
        },
    )


class MallOrderPayBody(BaseModel):
    order_id: str = ""
    pay_method: str = "balance"


@router_mall.post("/order/pay", response_model=APIResponse[dict])
def mobile_mall_order_pay(
    body: MallOrderPayBody,
    db: Session = Depends(get_db),
    user_id: int = Depends(mobile_user_id_from_header),
):
    """移动端：支付商城订单（余额扣款；微信/支付宝为开发态模拟成功）。"""
    try:
        oid = int(body.order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="订单无效")

    o = db.get(models.ProductOrder, oid)
    if not o or int(o.user_id) != int(user_id):
        raise HTTPException(status_code=404, detail="订单不存在")
    if o.pay_status == "paid":
        return APIResponse(
            code=0,
            msg="ok",
            data={"order_id": str(o.id), "order_no": o.order_no, "order_status": "paid", "message": "订单已支付"},
        )

    pm = (body.pay_method or o.pay_method or "balance").lower()
    if pm not in ("balance", "wechat", "alipay"):
        pm = "balance"

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=400, detail="用户不存在")

    for it in o.items:
        p = db.get(models.Product, it.product_id)
        if not p:
            raise HTTPException(status_code=400, detail="商品不存在")
        if int(p.stock or 0) < int(it.quantity):
            raise HTTPException(status_code=400, detail=f"库存不足：{p.name}")

    if pm == "balance":
        bal = user.balance if user.balance is not None else Decimal("0")
        if bal < o.amount_total:
            raise HTTPException(status_code=400, detail="余额不足，请先充值或选择其他支付方式")
        user.balance = bal - o.amount_total
    # wechat/alipay：不接真实收银台，直接走支付成功分支

    for it in o.items:
        p = db.get(models.Product, it.product_id)
        if p:
            p.stock = int(p.stock or 0) - int(it.quantity)

    o.pay_method = pm
    o.pay_status = "paid"
    o.pay_time = datetime.utcnow()

    db.commit()
    return APIResponse(
        code=0,
        msg="ok",
        data={"order_id": str(o.id), "order_no": o.order_no, "order_status": "paid", "message": "支付成功"},
    )


# ---------- account/recharge ----------
@router_account.get("/recharge/config", response_model=APIResponse[dict])
def mobile_recharge_config():
    """移动端：充值配置"""
    return APIResponse(code=0, msg="ok", data={"min_recharge_amount": 10.0, "recharge_tips": "所充金额可用于购买产品、网上祭祀、网上祈福等服务"})


class RechargeOrderCreateBody(BaseModel):
    recharge_amount: float = 0
    pay_method: str = "alipay"


@router_account.post("/recharge/order/create", response_model=APIResponse[dict])
def mobile_recharge_order_create(body: RechargeOrderCreateBody):
    """移动端：创建充值订单"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "order_no": "", "recharge_amount": body.recharge_amount, "pay_params": {}})


@router_account.get("/recharge/order/status", response_model=APIResponse[dict])
def mobile_recharge_order_status(order_id: str = Query(...)):
    """移动端：查询充值订单状态"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "order_status": "pending", "current_balance": 0})
