"""移动端接口 v1：商城 /api/mall/*, /api/account/recharge/*"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


class MallOrderCreateBody(BaseModel):
    product_id: str = ""
    quantity: int = 1
    address_id: str = ""


@router_mall.post("/order/create", response_model=APIResponse[dict])
def mobile_mall_order_create(body: MallOrderCreateBody):
    """移动端：立即购买创建订单"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "order_no": "", "total_amount": 0})


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
