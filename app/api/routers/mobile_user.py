"""移动端接口 v1：用户认证与个人中心 /api/user/*（App 端）"""
import base64
import random
import uuid
from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/user", tags=["Mobile-User"])


def _svg_captcha(text: str) -> str:
    w, h = 120, 40
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#f0f0f0"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" font-size="24" fill="#333" font-family="monospace">{text}</text></svg>'


# ---------- 认证（免鉴权）----------
@router.get("/captcha/image", response_model=APIResponse[dict])
def mobile_captcha_image():
    """移动端：获取图形验证码"""
    key = str(uuid.uuid4())
    text = "".join(str(random.randint(0, 9)) for _ in range(4))
    b64 = base64.b64encode(_svg_captcha(text).encode("utf-8")).decode("ascii")
    return APIResponse(code=0, msg="ok", data={"captcha_key": key, "captcha_image": f"data:image/svg+xml;base64,{b64}"})


class UserLoginBody(BaseModel):
    username: str = ""
    password: str = ""
    captcha: str = ""
    captcha_key: str = ""


@router.post("/login", response_model=APIResponse[dict])
def mobile_user_login(body: UserLoginBody):
    """移动端：用户登录（账号密码+验证码），返回 token 与 user_info。实际需校验验证码与用户表。"""
    # 存根：直接返回约定结构，后续对接 User 表与 JWT
    return APIResponse(code=0, msg="ok", data={
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "user_info": {"id": 1, "username": body.username or "user123", "nickname": "用户昵称", "avatar": "https://example.com/avatar.jpg"},
    })


class SmsSendBody(BaseModel):
    phone: str = ""
    captcha: str = ""
    captcha_key: str = ""


@router.post("/sms/send", response_model=APIResponse[dict])
def mobile_sms_send(body: SmsSendBody):
    """移动端：发送短信验证码"""
    return APIResponse(code=0, msg="ok", data={"sms_key": str(uuid.uuid4()), "expire_seconds": 60, "message": "验证码已发送"})


class LoginSmsBody(BaseModel):
    phone: str = ""
    sms_code: str = ""
    sms_key: str = ""
    agree_terms: bool = True


@router.post("/login/sms", response_model=APIResponse[dict])
def mobile_login_sms(body: LoginSmsBody):
    """移动端：短信验证码登录"""
    return APIResponse(code=0, msg="ok", data={
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "user_info": {"id": 1, "phone": body.phone, "nickname": "用户昵称", "avatar": "https://example.com/avatar.jpg"},
    })


class LoginPasswordBody(BaseModel):
    phone: str = ""
    password: str = ""
    captcha: str = ""
    captcha_key: str = ""
    agree_terms: bool = True


@router.post("/login/password", response_model=APIResponse[dict])
def mobile_login_password(body: LoginPasswordBody):
    """移动端：密码登录"""
    return APIResponse(code=0, msg="ok", data={
        "token": "eyJhbGciOiJIUzI1NiIs...",
        "user_info": {"id": 1, "phone": body.phone, "nickname": "用户昵称", "avatar": "https://example.com/avatar.jpg"},
    })


# ---------- 个人中心（需鉴权时由前端带 Bearer token，此处先返回存根）----------
@router.get("/info", response_model=APIResponse[dict])
def mobile_user_info():
    """移动端：获取当前用户信息"""
    return APIResponse(code=0, msg="ok", data={"user_id": "1", "username": "user123", "nickname": "用户昵称", "avatar": "https://example.com/avatar.jpg", "phone": "138****8000", "created_at": "2026-01-01 10:00:00"})


@router.get("/center/index", response_model=APIResponse[dict])
def mobile_center_index():
    """移动端：个人中心首页菜单等"""
    return APIResponse(code=0, msg="ok", data={
        "menus": [
            {"menu_code": "order_list", "menu_name": "我的订单"},
            {"menu_code": "cart", "menu_name": "购物车"},
            {"menu_code": "profile", "menu_name": "个人资料"},
            {"menu_code": "blessing_records", "menu_name": "祈福记录"},
            {"menu_code": "memorial_records", "menu_name": "祭祀记录"},
            {"menu_code": "credit_card", "menu_name": "绑定信用卡"},
            {"menu_code": "balance_records", "menu_name": "账变记录"},
        ],
    })


class ProfileUpdateBody(BaseModel):
    nickname: str = ""
    avatar: str = ""
    gender: str = ""
    birthday: str = ""
    address: str = ""


@router.post("/profile/update", response_model=APIResponse[dict])
def mobile_profile_update(body: ProfileUpdateBody):
    """移动端：更新个人资料"""
    return APIResponse(code=0, msg="ok", data={"message": "更新成功"})


@router.get("/profile/detail", response_model=APIResponse[dict])
def mobile_profile_detail():
    """移动端：个人资料详情"""
    return APIResponse(code=0, msg="ok", data={"user_id": 1, "account": "13789898989", "nickname": "用户昵称", "avatar": "https://example.com/avatar.jpg", "balance": 0.0})


class NicknameUpdateBody(BaseModel):
    nickname: str = ""


@router.post("/profile/nickname/update", response_model=APIResponse[dict])
def mobile_profile_nickname_update(body: NicknameUpdateBody):
    """移动端：修改昵称"""
    return APIResponse(code=0, msg="ok", data={"message": "修改成功"})


class PasswordUpdateBody(BaseModel):
    old_password: str = ""
    new_password: str = ""


@router.post("/password/update", response_model=APIResponse[dict])
def mobile_password_update(body: PasswordUpdateBody):
    """移动端：修改登录密码"""
    return APIResponse(code=0, msg="ok", data={"message": "密码修改成功，请重新登录"})


@router.get("/blessing/records", response_model=APIResponse[dict])
def mobile_blessing_records(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    method_type: str | None = Query(None),
):
    """移动端：祈福记录列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "page_num": page_num, "page_size": page_size, "list": []})


@router.get("/memorial/records", response_model=APIResponse[dict])
def mobile_memorial_records(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    offering_type: str | None = Query(None),
):
    """移动端：祭祀记录列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "page_num": page_num, "page_size": page_size, "list": []})


class BankcardBindBody(BaseModel):
    card_no: str = ""
    card_holder: str = ""
    expire_date: str = ""
    cvv: str = ""
    phone: str = ""


@router.post("/bankcard/bind", response_model=APIResponse[dict])
def mobile_bankcard_bind(body: BankcardBindBody):
    """移动端：绑定银行卡/信用卡"""
    return APIResponse(code=0, msg="ok", data={"card_id": str(uuid.uuid4()), "message": "绑定成功"})


@router.get("/balance/records", response_model=APIResponse[dict])
def mobile_balance_records(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    record_type: str | None = Query(None),
):
    """移动端：账变记录"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "page_num": page_num, "page_size": page_size, "list": []})


# ---------- 购物车 ----------
@router.get("/cart/list", response_model=APIResponse[dict])
def mobile_cart_list():
    """移动端：购物车列表"""
    return APIResponse(code=0, msg="ok", data={"total_count": 0, "selected_count": 0, "list": []})


class CartQuantityBody(BaseModel):
    cart_id: str = ""
    quantity: int = 1


@router.post("/cart/quantity/update", response_model=APIResponse[dict])
def mobile_cart_quantity_update(body: CartQuantityBody):
    """移动端：更新购物车数量"""
    return APIResponse(code=0, msg="ok", data={"cart_id": body.cart_id, "subtotal": 0, "message": "更新成功"})


class CartDeleteBody(BaseModel):
    cart_id: str = ""


@router.post("/cart/delete", response_model=APIResponse[dict])
def mobile_cart_delete(body: CartDeleteBody):
    """移动端：删除购物车项"""
    return APIResponse(code=0, msg="ok", data={"message": "删除成功"})


class CartSelectBody(BaseModel):
    cart_id: str = ""
    selected: bool = True


@router.post("/cart/select", response_model=APIResponse[dict])
def mobile_cart_select(body: CartSelectBody):
    """移动端：选中/取消选中商品"""
    return APIResponse(code=0, msg="ok", data={"message": "操作成功"})


class CartSelectAllBody(BaseModel):
    selected: bool = True


@router.post("/cart/select/all", response_model=APIResponse[dict])
def mobile_cart_select_all(body: CartSelectAllBody):
    """移动端：全选/取消全选"""
    return APIResponse(code=0, msg="ok", data={"message": "操作成功"})


@router.get("/cart/calculate", response_model=APIResponse[dict])
def mobile_cart_calculate():
    """移动端：购物车结算价"""
    return APIResponse(code=0, msg="ok", data={"total_count": 0, "selected_count": 0, "total_amount": 0})


class CartCheckoutBody(BaseModel):
    cart_ids: list[str] = []


@router.post("/cart/checkout", response_model=APIResponse[dict])
def mobile_cart_checkout(body: CartCheckoutBody):
    """移动端：购物车结算"""
    return APIResponse(code=0, msg="ok", data={"order_id": str(uuid.uuid4()), "total_amount": 0, "message": "ok"})


# ---------- 订单 ----------
@router.get("/order/list", response_model=APIResponse[dict])
def mobile_order_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    order_status: str | None = Query(None),
):
    """移动端：我的订单列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "page_num": page_num, "page_size": page_size, "list": []})


@router.get("/order/detail", response_model=APIResponse[dict])
def mobile_order_detail(order_id: str = Query(...)):
    """移动端：订单详情"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "order_no": "", "order_status": "pending", "list": []})


# ---------- 地址 ----------
@router.get("/address/list", response_model=APIResponse[dict])
def mobile_address_list():
    """移动端：收货地址列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


class AddressAddBody(BaseModel):
    receiver_name: str = ""
    receiver_phone: str = ""
    country_id: str = "CN"
    province_id: str = ""
    city_id: str = ""
    district_id: str = ""
    detail_address: str = ""
    is_default: bool = False


@router.post("/address/add", response_model=APIResponse[dict])
def mobile_address_add(body: AddressAddBody):
    """移动端：新增收货地址"""
    return APIResponse(code=0, msg="ok", data={"address_id": str(uuid.uuid4()), "create_time": "", "message": "地址添加成功"})


class AddressUpdateBody(AddressAddBody):
    address_id: str = ""


@router.post("/address/update", response_model=APIResponse[dict])
def mobile_address_update(body: AddressUpdateBody):
    """移动端：修改收货地址"""
    return APIResponse(code=0, msg="ok", data={"address_id": body.address_id, "message": "地址修改成功"})


class AddressDeleteBody(BaseModel):
    address_id: str = ""


@router.post("/address/delete", response_model=APIResponse[dict])
def mobile_address_delete(body: AddressDeleteBody):
    """移动端：删除收货地址"""
    return APIResponse(code=0, msg="ok", data={"message": "地址删除成功"})


@router.post("/address/set_default", response_model=APIResponse[dict])
def mobile_address_set_default(body: AddressDeleteBody):
    """移动端：设置默认地址"""
    return APIResponse(code=0, msg="ok", data={"message": "已设置为默认地址"})


# ---------- 信用卡 ----------
@router.get("/credit_card/list", response_model=APIResponse[dict])
def mobile_credit_card_list():
    """移动端：已绑信用卡列表"""
    return APIResponse(code=0, msg="ok", data={"list": []})


class CreditCardAddBody(BaseModel):
    card_holder_name: str = ""
    card_number: str = ""
    expiry_date: str = ""
    cvv: str = ""
    phone_number: str = ""
    is_default: bool = False
    sms_code: str = ""
    bank_id: str = ""


@router.post("/credit_card/add", response_model=APIResponse[dict])
def mobile_credit_card_add(body: CreditCardAddBody):
    """移动端：新增信用卡"""
    return APIResponse(code=0, msg="ok", data={"card_id": str(uuid.uuid4()), "card_number_masked": "**** **** **** 3452", "message": "信用卡绑定成功"})


class CreditCardDeleteBody(BaseModel):
    card_id: str = ""


@router.post("/credit_card/delete", response_model=APIResponse[dict])
def mobile_credit_card_delete(body: CreditCardDeleteBody):
    """移动端：删除信用卡"""
    return APIResponse(code=0, msg="ok", data={"message": "删除成功"})


@router.post("/credit_card/set_default", response_model=APIResponse[dict])
def mobile_credit_card_set_default(body: CreditCardDeleteBody):
    """移动端：设置默认信用卡"""
    return APIResponse(code=0, msg="ok", data={"message": "已设置为默认卡"})


@router.get("/credit_card/banks", response_model=APIResponse[dict])
def mobile_credit_card_banks():
    """移动端：支持绑定的银行列表"""
    return APIResponse(code=0, msg="ok", data={"list": [{"bank_id": "ICBC", "bank_name": "中国工商银行", "bank_logo": ""}]})


class CreditCardSendSmsBody(BaseModel):
    card_number: str = ""
    phone_number: str = ""


@router.post("/credit_card/send_sms", response_model=APIResponse[dict])
def mobile_credit_card_send_sms(body: CreditCardSendSmsBody):
    """移动端：发送绑卡验证码"""
    return APIResponse(code=0, msg="ok", data={"sent": True, "expired_in": 60, "message": "验证码已发送"})


@router.get("/credit_card/list_for_pay", response_model=APIResponse[dict])
def mobile_credit_card_list_for_pay():
    """移动端：支付时可选信用卡列表"""
    return APIResponse(code=0, msg="ok", data={"list": []})


# ---------- 密码（找回/修改）----------
@router.post("/password/send_sms", response_model=APIResponse[dict])
def mobile_password_send_sms():
    """移动端：发送修改密码验证码"""
    return APIResponse(code=0, msg="ok", data={"sent": True, "expired_in": 60, "message": "验证码已发送"})


class PasswordChangeBody(BaseModel):
    new_password: str = ""
    confirm_password: str = ""
    sms_code: str = ""


@router.post("/password/change", response_model=APIResponse[dict])
def mobile_password_change(body: PasswordChangeBody):
    """移动端：验证码修改密码"""
    return APIResponse(code=0, msg="ok", data={"changed": True, "message": "密码修改成功", "redirect_url": "/login"})


# ---------- 钱包/充值 ----------
@router.get("/wallet/transactions", response_model=APIResponse[dict])
def mobile_wallet_transactions(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    type: str | None = Query(None),
):
    """移动端：钱包流水"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


class WalletRechargeCreateBody(BaseModel):
    amount: float = 0
    pay_method: str = "alipay"


@router.post("/wallet/recharge/create", response_model=APIResponse[dict])
def mobile_wallet_recharge_create(body: WalletRechargeCreateBody):
    """移动端：创建充值订单"""
    return APIResponse(code=0, msg="ok", data={"order_id": str(uuid.uuid4()), "order_no": "", "amount": body.amount, "pay_params": {}})


@router.post("/wallet/recharge/qrcode", response_model=APIResponse[dict])
def mobile_wallet_recharge_qrcode(body: dict):
    """移动端：获取充值支付二维码"""
    return APIResponse(code=0, msg="ok", data={"qr_code": "", "order_id": ""})


@router.post("/wallet/recharge/cancel", response_model=APIResponse[dict])
def mobile_wallet_recharge_cancel(body: dict):
    """移动端：取消充值订单"""
    return APIResponse(code=0, msg="ok", data={"message": "已取消"})


@router.post("/wallet/recharge/later", response_model=APIResponse[dict])
def mobile_wallet_recharge_later(body: dict):
    """移动端：稍后支付"""
    return APIResponse(code=0, msg="ok", data={"message": "ok"})


@router.get("/wallet/recharge/status", response_model=APIResponse[dict])
def mobile_wallet_recharge_status(order_id: str = Query(...)):
    """移动端：查询充值订单状态"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "status": "pending", "balance": 0})


# ---------- 测算记录 ----------
@router.get("/divination/records", response_model=APIResponse[dict])
def mobile_divination_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    divination_type: str | None = Query(None),
):
    """移动端：用户测算记录"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})
