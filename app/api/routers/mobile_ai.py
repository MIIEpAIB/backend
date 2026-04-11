"""移动端接口 v1：AI 测算 /api/ai/divination/*（接入 DeepSeek）"""
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.deepseek import chat as deepseek_chat
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/ai/divination", tags=["Mobile-AI"])


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _call_ai(system: str, user: str) -> str:
    try:
        return deepseek_chat(system, user)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}")


class DrawBody(BaseModel):
    question: str = ""
    divination_type: str = "lottery"


@router.post("/draw", response_model=APIResponse[dict])
def mobile_ai_draw(body: DrawBody):
    """移动端：抽签（DeepSeek 解签）"""
    sys = "你是传统文化中的解签师，根据用户问题给出一个签位（上上/上吉/中平/下等）、简短签文和通俗解释。用中文回答，签文可带一点古文韵味，解释要亲切易懂。"
    user = f"问事类型：{body.divination_type or 'lottery'}。用户问题：{body.question or '求签'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "result_id": str(uuid4()),
            "sign_title": "上上签",
            "sign_content": text.split("\n")[0] if text else "签文内容",
            "interpretation": text,
            "created_at": _now(),
        },
    )


class BaziBody(BaseModel):
    name: str = ""
    gender: str = "male"
    birth_date: str = ""
    birth_time: str = ""
    birth_place: str = ""


@router.post("/bazi", response_model=APIResponse[dict])
def mobile_ai_bazi(body: BaziBody):
    """移动端：八字算命（DeepSeek）"""
    sys = "你是八字命理师，根据用户提供的出生信息，用中文简要分析命盘特点、性格与运势趋势。保持专业但易懂，避免过度断言。"
    user = f"姓名：{body.name}，性别：{body.gender}，出生日期：{body.birth_date}，出生时辰：{body.birth_time}，出生地：{body.birth_place}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "result_id": str(uuid4()),
            "bazi_info": {},
            "life_analysis": text,
            "fortune_trend": {},
            "created_at": _now(),
        },
    )


class FengshuiBody(BaseModel):
    address: str = ""
    direction: str = ""


@router.post("/fengshui", response_model=APIResponse[dict])
def mobile_ai_fengshui(body: FengshuiBody):
    """移动端：风水测算（DeepSeek）"""
    sys = "你是风水顾问，根据地址和朝向用中文给出简明风水分析与建议。语气专业、温和，避免绝对化结论。"
    user = f"地址：{body.address}，朝向：{body.direction}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "analysis": text, "created_at": _now()},
    )


class DreamBody(BaseModel):
    dream_content: str = ""


@router.post("/dream", response_model=APIResponse[dict])
def mobile_ai_dream(body: DreamBody):
    """移动端：解梦（DeepSeek）"""
    sys = "你是解梦师，结合传统文化与常见象征，对用户描述的梦境用中文做简短、正向的解读，仅供娱乐参考。"
    user = f"梦境描述：{body.dream_content or '未描述'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "interpretation": text, "created_at": _now()},
    )


class CharBody(BaseModel):
    character: str = ""
    purpose_code: str = ""


@router.post("/char", response_model=APIResponse[dict])
def mobile_ai_char(body: CharBody):
    """移动端：测字（DeepSeek）"""
    sys = "你是测字师，根据用户写的一个字和问事目的（如财运、姻缘），用中文从字形、字义、寓意给出简短解读，语气温和。"
    user = f"字：{body.character or '未提供'}，问事类型：{body.purpose_code or '一般'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "analysis": text, "created_at": _now()},
    )


class NamingBody(BaseModel):
    surname: str = ""
    gender: str = "male"


@router.post("/naming", response_model=APIResponse[dict])
def mobile_ai_naming(body: NamingBody):
    """移动端：取名（DeepSeek）"""
    sys = "你是起名顾问，根据姓氏和性别，用中文给出 3～5 个名字建议，并简要说明寓意与五行/笔画考量。名字需文雅、好记、无生僻字。"
    user = f"姓氏：{body.surname}，性别：{body.gender}"
    text = _call_ai(sys, user)
    names = [n.strip() for n in text.replace("、", " ").split() if len(n.strip()) >= 2][:5]
    if not names:
        names = ["请查看下方分析"]
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "names": names, "created_at": _now(), "analysis": text},
    )


class PhoneBody(BaseModel):
    phone_number: str = ""


@router.post("/phone", response_model=APIResponse[dict])
def mobile_ai_phone(body: PhoneBody):
    """移动端：手机号测算（DeepSeek）"""
    sys = "你是数字能量/号码解读顾问，对用户提供的手机号用中文做简短、正向的解读（如数字寓意、易记性等），仅供娱乐参考。"
    user = f"手机号：{body.phone_number or '未提供'}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "analysis": text, "created_at": _now()},
    )


class MediaBody(BaseModel):
    media_type: str = ""
    media_url: str = ""


@router.post("/media", response_model=APIResponse[dict])
def mobile_ai_media(body: MediaBody):
    """移动端：媒体类测算（DeepSeek，根据类型与描述解读）"""
    sys = "你是传统文化与命理顾问，根据用户上传的媒体类型和简要描述（如手相、面相、签文照片等），用中文给出简短、正向的解读，仅供娱乐参考。若信息不足则说明需要更多描述。"
    user = f"类型：{body.media_type}，链接或描述：{body.media_url}"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={"result_id": str(uuid4()), "analysis": text, "created_at": _now()},
    )
