"""移动端接口 v1：风水、教学、解梦、商城订单、祈福、取名、手机、首页、商品、订单、支付、地区、协议、认证、专家（解梦/取名/手机/运势接入 DeepSeek）"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.core.deepseek import chat as deepseek_chat
from backend.app.schemas.common import APIResponse


def _call_ai(system: str, user: str) -> str:
    try:
        return deepseek_chat(system, user)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}")

# 风水
router_fengshui = APIRouter(prefix="/api/fengshui", tags=["Mobile-Fengshui"])


@router_fengshui.get("/category/tree", response_model=APIResponse[dict])
def mobile_fengshui_category_tree():
    """移动端：风水分类树"""
    return APIResponse(code=0, msg="ok", data={"tree": []})


@router_fengshui.get("/search", response_model=APIResponse[dict])
def mobile_fengshui_search(
    keyword: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：风水搜索"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router_fengshui.get("/detail", response_model=APIResponse[dict])
def mobile_fengshui_detail(content_id: str = Query(...)):
    """移动端：风水详情"""
    return APIResponse(code=0, msg="ok", data={"content_id": content_id, "title": "", "content": ""})


# 解梦
router_dream = APIRouter(prefix="/api/dream", tags=["Mobile-Dream"])


class DreamInterpretBody(BaseModel):
    dream_keyword: str = ""
    dream_content: str = ""


@router_dream.post("/interpret", response_model=APIResponse[dict])
def mobile_dream_interpret(body: DreamInterpretBody):
    """移动端：解梦（DeepSeek）"""
    sys = "你是解梦师，结合传统文化与常见象征，对用户描述的梦境用中文做简短、正向的解读，仅供娱乐参考。"
    user = f"关键词：{body.dream_keyword}；梦境描述：{body.dream_content or '未描述'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"dream_id": str(uuid4()), "interpretation": text, "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    )


@router_dream.get("/history/list", response_model=APIResponse[dict])
def mobile_dream_history_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：解梦历史"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


# 商城订单（store）
router_store = APIRouter(prefix="/api/store", tags=["Mobile-Store"])


@router_store.get("/order/confirm", response_model=APIResponse[dict])
def mobile_store_order_confirm(product_id: str = Query(...), quantity: int = Query(1, ge=1)):
    """移动端：订单确认页数据"""
    return APIResponse(code=0, msg="ok", data={"product_info": {}, "address_list": [], "payment_methods": []})


class StoreOrderSubmitBody(BaseModel):
    product_id: str = ""
    quantity: int = 1
    address_id: str = ""
    pay_method: str = "alipay"


@router_store.post("/order/submit", response_model=APIResponse[dict])
def mobile_store_order_submit(body: StoreOrderSubmitBody):
    """移动端：提交订单"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "order_no": "", "total_amount": 0})


class StoreOrderPayBody(BaseModel):
    order_id: str = ""
    pay_method: str = "alipay"


@router_store.post("/order/pay", response_model=APIResponse[dict])
def mobile_store_order_pay(body: StoreOrderPayBody):
    """移动端：发起支付"""
    return APIResponse(code=0, msg="ok", data={"order_id": body.order_id, "order_status": "pending", "pay_params": {}})


# 祈福（移动端 App 用，与后台 blessing 并存）
router_blessing = APIRouter(prefix="/api/blessing", tags=["Mobile-Blessing"])


@router_blessing.get("/methods/list", response_model=APIResponse[list])
def mobile_blessing_methods_list():
    """移动端：祈福方式列表"""
    return APIResponse(code=0, msg="ok", data=[{"method_id": "1", "method_name": "上香", "method_image": "", "price_coins": 1}])


@router_blessing.get("/feed/list", response_model=APIResponse[dict])
def mobile_blessing_feed_list(
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：祈福动态列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


class BlessingSubmitBody(BaseModel):
    method_id: str = ""
    blessing_content: str = ""
    quantity: int = 1


@router_blessing.post("/submit", response_model=APIResponse[dict])
def mobile_blessing_submit(body: BlessingSubmitBody):
    """移动端：提交祈福"""
    return APIResponse(code=0, msg="ok", data={"record_id": "uuid", "total_cost_coins": 0, "current_balance": 0, "message": "祈福成功"})


# 取名、手机、首页、商品、订单、支付、地区、协议、认证、专家
router_naming = APIRouter(prefix="/api/naming", tags=["Mobile-Naming"])
router_phone = APIRouter(prefix="/api/phone", tags=["Mobile-Phone"])
router_home = APIRouter(prefix="/api/home", tags=["Mobile-Home"])
router_product = APIRouter(prefix="/api/product", tags=["Mobile-Product"])
router_order = APIRouter(prefix="/api/order", tags=["Mobile-Order"])
router_payment = APIRouter(prefix="/api/payment", tags=["Mobile-Payment"])
router_cart = APIRouter(prefix="/api/cart", tags=["Mobile-Cart"])
router_logistics = APIRouter(prefix="/api/logistics", tags=["Mobile-Logistics"])
router_region = APIRouter(prefix="/api/region", tags=["Mobile-Region"])
router_metaphysics = APIRouter(prefix="/api/metaphysics", tags=["Mobile-Metaphysics"])
router_agreement = APIRouter(prefix="/api/agreement", tags=["Mobile-Agreement"])
router_auth = APIRouter(prefix="/api/auth", tags=["Mobile-Auth"])
router_expert = APIRouter(prefix="/api/expert", tags=["Mobile-Expert"])
router_fortune = APIRouter(prefix="/api/fortune", tags=["Mobile-Fortune"])


class NamingCalculateBody(BaseModel):
    surname: str = ""
    gender: str = "male"


@router_naming.post("/calculate", response_model=APIResponse[dict])
def mobile_naming_calculate(body: NamingCalculateBody):
    """移动端：取名测算（DeepSeek）"""
    sys = "你是起名顾问，根据姓氏和性别，用中文给出 3～5 个名字建议，并简要说明寓意。名字需文雅、好记、无生僻字。"
    user = f"姓氏：{body.surname}，性别：{body.gender}"
    text = _call_ai(sys, user)
    names = [n.strip() for n in text.replace("、", " ").split() if len(n.strip()) >= 2][:5]
    if not names:
        names = ["请查看下方分析"]
    return APIResponse(code=0, msg="ok", data={"result_id": str(uuid4()), "names": names, "analysis": text})


class PhoneCalculateBody(BaseModel):
    phone_number: str = ""


@router_phone.post("/calculate", response_model=APIResponse[dict])
def mobile_phone_calculate(body: PhoneCalculateBody):
    """移动端：手机号测算（DeepSeek）"""
    sys = "你是数字能量/号码解读顾问，对用户提供的手机号用中文做简短、正向的解读（如数字寓意、易记性等），仅供娱乐参考。"
    user = f"手机号：{body.phone_number or '未提供'}"
    text = _call_ai(sys, user)
    return APIResponse(code=0, msg="ok", data={"result_id": str(uuid4()), "analysis": text})


@router_home.get("/init", response_model=APIResponse[dict])
def mobile_home_init():
    """移动端：首页初始化"""
    return APIResponse(code=0, msg="ok", data={"banners": [], "modules": []})


@router_product.get("/hot", response_model=APIResponse[dict])
def mobile_product_hot():
    """移动端：热门商品"""
    return APIResponse(code=0, msg="ok", data={"list": []})


@router_product.get("/detail", response_model=APIResponse[dict])
def mobile_product_detail(product_id: str = Query(...)):
    """移动端：商品详情"""
    return APIResponse(code=0, msg="ok", data={"product_id": product_id, "product_name": "", "price": 0})


@router_product.get("/recommend", response_model=APIResponse[dict])
def mobile_product_recommend():
    """移动端：推荐商品"""
    return APIResponse(code=0, msg="ok", data={"list": []})


@router_order.get("/detail", response_model=APIResponse[dict])
def mobile_order_detail(order_id: str = Query(...)):
    """移动端：订单详情（通用）"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "order_status": "", "list": []})


class OrderCancelBody(BaseModel):
    order_id: str = ""


@router_order.post("/cancel", response_model=APIResponse[dict])
def mobile_order_cancel(body: OrderCancelBody):
    """移动端：取消订单"""
    return APIResponse(code=0, msg="ok", data={"message": "已取消"})


@router_order.post("/later", response_model=APIResponse[dict])
def mobile_order_later(body: OrderCancelBody):
    """移动端：稍后支付"""
    return APIResponse(code=0, msg="ok", data={"message": "ok"})


@router_order.get("/logistics", response_model=APIResponse[dict])
def mobile_order_logistics(order_id: str = Query(...)):
    """移动端：物流信息"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "traces": []})


class OrderConfirmBody(BaseModel):
    order_id: str = ""


@router_order.post("/confirm", response_model=APIResponse[dict])
def mobile_order_confirm(body: OrderConfirmBody):
    """移动端：确认收货"""
    return APIResponse(code=0, msg="ok", data={"message": "确认收货成功"})


class OrderCreateBody(BaseModel):
    product_id: str = ""
    quantity: int = 1
    address_id: str = ""


@router_order.post("/create", response_model=APIResponse[dict])
def mobile_order_create(body: OrderCreateBody):
    """移动端：创建订单"""
    return APIResponse(code=0, msg="ok", data={"order_id": "uuid", "order_no": "", "total_amount": 0})


class PaymentQrcodeBody(BaseModel):
    order_id: str = ""
    pay_method: str = "alipay"


@router_payment.post("/qrcode", response_model=APIResponse[dict])
def mobile_payment_qrcode(body: PaymentQrcodeBody):
    """移动端：获取支付二维码"""
    return APIResponse(code=0, msg="ok", data={"qr_code": "", "order_id": body.order_id})


@router_payment.get("/status", response_model=APIResponse[dict])
def mobile_payment_status(order_id: str = Query(...)):
    """移动端：支付状态查询"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "status": "pending"})


class PaymentCreditCardSmsBody(BaseModel):
    order_id: str = ""
    card_id: str = ""


@router_payment.post("/credit_card/send_sms", response_model=APIResponse[dict])
def mobile_payment_credit_card_send_sms(body: PaymentCreditCardSmsBody):
    """移动端：支付验证码"""
    return APIResponse(code=0, msg="ok", data={"sent": True, "expired_in": 60})


class PaymentCreditCardPayBody(BaseModel):
    order_id: str = ""
    card_id: str = ""
    sms_code: str = ""


@router_payment.post("/credit_card/pay", response_model=APIResponse[dict])
def mobile_payment_credit_card_pay(body: PaymentCreditCardPayBody):
    """移动端：信用卡支付"""
    return APIResponse(code=0, msg="ok", data={"order_id": body.order_id, "order_status": "paid", "message": "支付成功"})


class CartAddBody(BaseModel):
    product_id: str = ""
    quantity: int = 1


@router_cart.post("/add", response_model=APIResponse[dict])
def mobile_cart_add(body: CartAddBody):
    """移动端：加入购物车（短路径）"""
    return APIResponse(code=0, msg="ok", data={"cart_id": "uuid", "message": "加入购物车成功"})


@router_logistics.get("/detail", response_model=APIResponse[dict])
def mobile_logistics_detail(order_id: str = Query(...)):
    """移动端：物流详情"""
    return APIResponse(code=0, msg="ok", data={"order_id": order_id, "company": "", "tracking_no": "", "traces": []})


@router_region.get("/countries", response_model=APIResponse[list])
def mobile_region_countries():
    """移动端：国家列表"""
    return APIResponse(code=0, msg="ok", data=[{"country_id": "CN", "country_name": "中国"}])


@router_region.get("/provinces", response_model=APIResponse[list])
def mobile_region_provinces(country_id: str = Query("CN")):
    """移动端：省份列表"""
    return APIResponse(code=0, msg="ok", data=[])


@router_region.get("/cities", response_model=APIResponse[list])
def mobile_region_cities(province_id: str = Query(...)):
    """移动端：城市列表"""
    return APIResponse(code=0, msg="ok", data=[])


@router_region.get("/districts", response_model=APIResponse[list])
def mobile_region_districts(city_id: str = Query(...)):
    """移动端：区县列表"""
    return APIResponse(code=0, msg="ok", data=[])


@router_metaphysics.get("/categories", response_model=APIResponse[dict])
def mobile_metaphysics_categories():
    """移动端：玄学分类（可与后台 category/list 数据源一致）"""
    return APIResponse(code=0, msg="ok", data={"list": [{"category_id": "news", "category_name": "玄学新闻"}]})


@router_metaphysics.get("/articles", response_model=APIResponse[dict])
def mobile_metaphysics_articles(
    category_id: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """移动端：文章列表"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "page_num": page_num, "page_size": page_size, "list": []})


@router_metaphysics.get("/article/detail", response_model=APIResponse[dict])
def mobile_metaphysics_article_detail(article_id: str = Query(...)):
    """移动端：文章详情"""
    return APIResponse(code=0, msg="ok", data={"article_id": article_id, "title": "", "content": ""})


@router_agreement.get("/privacy", response_model=APIResponse[dict])
def mobile_agreement_privacy():
    """移动端：隐私协议"""
    return APIResponse(code=0, msg="ok", data={"title": "隐私协议", "content": ""})


@router_agreement.get("/user_agreement", response_model=APIResponse[dict])
def mobile_agreement_user():
    """移动端：用户协议"""
    return APIResponse(code=0, msg="ok", data={"title": "用户协议", "content": ""})


class AuthRegisterSendSmsBody(BaseModel):
    mobile: str = ""


@router_auth.post("/register/send_sms", response_model=APIResponse[dict])
def mobile_auth_register_send_sms(body: AuthRegisterSendSmsBody):
    """移动端：注册发送验证码"""
    return APIResponse(code=0, msg="ok", data={"expire": 180})


class AuthRegisterBody(BaseModel):
    mobile: str = ""
    password: str = ""
    confirm_password: str = ""
    captcha: str = ""


@router_auth.post("/register", response_model=APIResponse[dict])
def mobile_auth_register(body: AuthRegisterBody):
    """移动端：用户注册"""
    return APIResponse(code=0, msg="ok", data={"user_id": 10086, "mobile": body.mobile})


@router_expert.get("/categories", response_model=APIResponse[dict])
def mobile_expert_categories():
    """移动端：专家分类"""
    return APIResponse(code=0, msg="ok", data={"list": []})


@router_expert.get("/master/detail", response_model=APIResponse[dict])
def mobile_expert_master_detail(master_id: str = Query(...)):
    """移动端：专家详情"""
    return APIResponse(code=0, msg="ok", data={"master_id": master_id, "name": "", "avatar": "", "intro": ""})


@router_expert.get("/platform/info", response_model=APIResponse[dict])
def mobile_expert_platform_info():
    """移动端：平台联系信息"""
    return APIResponse(code=0, msg="ok", data={"phone": "", "email": ""})


class ExpertContactBody(BaseModel):
    expert_id: str = ""
    message: str = ""
    contact: str = ""


@router_expert.post("/contact", response_model=APIResponse[dict])
def mobile_expert_contact(body: ExpertContactBody):
    """移动端：联系专家"""
    return APIResponse(code=0, msg="ok", data={"message": "提交成功"})


@router_fortune.get("/init", response_model=APIResponse[dict])
def mobile_fortune_init():
    """移动端：运势首页"""
    return APIResponse(code=0, msg="ok", data={"modules": [], "banners": []})


class FortuneCalculateBody(BaseModel):
    birth_date: str = ""
    birth_time: str = ""
    purpose_code: str = ""


@router_fortune.post("/calculate", response_model=APIResponse[dict])
def mobile_fortune_calculate(body: FortuneCalculateBody):
    """移动端：运势测算（DeepSeek）"""
    sys = "你是运势顾问，根据用户出生日期与问事类型，用中文给出近期运势概要（事业、感情、健康、财运等），语气温和、正向，仅供娱乐参考。"
    user = f"出生日期：{body.birth_date}，出生时辰：{body.birth_time}，问事类型：{body.purpose_code or '综合'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "summary": text[:200] if text else "", "details": {"full_analysis": text}},
    )
