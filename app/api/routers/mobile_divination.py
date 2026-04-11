"""移动端接口 v1：测字/抽签 /api/divination/*, /api/lottery/*（测字：易经卦象 + 付费解锁详批；抽签接 DeepSeek）"""
from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.app.core.deepseek import chat as deepseek_chat
from backend.app.core.iching_kw64 import KW_HEXAGRAM_NAMES
from backend.app.schemas.common import APIResponse

router_div = APIRouter(prefix="/api/divination", tags=["Mobile-Divination"])
router_lot = APIRouter(prefix="/api/lottery", tags=["Mobile-Lottery"])

# 测字会话（内存）：真实支付上线后可改为 Redis/DB + 验签
_char_sessions: dict[str, dict] = {}

PURPOSE_NAMES: dict[str, str] = {
    "fortune": "问财运",
    "marriage": "问姻缘",
    "health": "问健康",
    "career": "问前程",
    "study": "问学业",
}

UNLOCK_PRICE_CNY = 9.9


def _call_ai(system: str, user: str) -> str:
    try:
        return deepseek_chat(system, user)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}")


def _hexagram_index(character: str, purpose_code: str) -> int:
    raw = f"{character or '问'}|{purpose_code or 'general'}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 64


def _hexagram_brief(name: str) -> str:
    """卦象一句象辞（与《易传》大意相近的泛化表述，非实占排盘）。"""
    if name.startswith("乾"):
        return "天行健，君子以自强不息。"
    if name.startswith("坤"):
        return "地势坤，君子以厚德载物。"
    if "坎" in name and "水" in name:
        return "水流而不盈，行险而不失其信，宜以诚信处变。"
    if "离" in name and "火" in name:
        return "明两作，大人以继明照于四方，宜明辨是非、持中守正。"
    return "观象玩辞，以察吉凶；因时制宜，守中持正。"


def _mock_overview(character: str, purpose_name: str, hex_name: str) -> str:
    return (
        f"以「{character}」字起象，得「{hex_name}」。"
        f"所问「{purpose_name}」：卦气显示当前重在蓄势与调顺，宜先定心、后谋动，"
        "不宜躁进。以下为卦象纲要，细批爻辞与方位宜忌需解锁后查看。"
    )


def _mock_detail(character: str, purpose_name: str, hex_name: str) -> dict:
    return {
        "hexagram_comment": (
            f"「{hex_name}」与所测之字「{character}」相参：卦体上下交应，主事象在「气机升降」之间。"
            f"就「{purpose_name}」而言，近期多见反复，然反复之中自有转机；"
            "宜以静制动，先理清利害与主次，再定一步一策之行动。"
        ),
        "yao_ci": (
            "初爻：宜潜藏蓄势，勿轻举妄动。\n"
            "二爻：可得小助，宜以谦和待人，广结善缘。\n"
            "三爻：反复之象，慎言慎行，忌争讼与冲动决策。\n"
            "四爻：转机渐显，宜把握窗口，但不可贪多。\n"
            "五爻：守中得正，以德服人，事可渐顺。\n"
            "上爻：物极必反，宜知止，留有余地。"
        ),
        "auspicious_direction": (
            "吉方：东南（宜布置书桌、洽谈、静修）。\n"
            "忌方：正西（忌久坐久争、忌口舌是非）。\n"
            "（以上为事理类比之方位建议，非风水实地勘测结论。）"
        ),
        "action_advice": (
            "行动建议：\n"
            "1）先复盘资源与风险，列出三条可执行的小目标；\n"
            "2）重要承诺延后三日再定，避免情绪决策；\n"
            "3）宜以「信」与「和」破局：对内守信，对外以和为贵。"
        ),
    }


def _overview_ai_or_mock(character: str, purpose_name: str, hex_name: str) -> str:
    try:
        text = deepseek_chat(
            "你是易学顾问。请用中文写「测字总览」共 2～4 句，风格偏易经，典雅简练。"
            "只写卦意纲要，不要写爻辞、不要写吉凶方位、不要写行动建议条目。",
            f"所测之字：{character}。问事：{purpose_name}。所得卦名：{hex_name}。",
        )
        if text and len(text.strip()) >= 8:
            return text.strip()
    except Exception:
        pass
    return _mock_overview(character, purpose_name, hex_name)


@router_div.get("/purpose/list", response_model=APIResponse[list])
def mobile_divination_purpose_list():
    """移动端：测字目的选项"""
    return APIResponse(code=0, msg="ok", data=[{"purpose_code": "fortune", "purpose_name": "问财运"}, {"purpose_code": "marriage", "purpose_name": "问姻缘"}])


class CharacterCalculateBody(BaseModel):
    character: str = ""
    purpose_code: str = ""


@router_div.post("/character/calculate", response_model=APIResponse[dict])
def mobile_character_calculate(body: CharacterCalculateBody):
    """
    测字：易经卦象格式。
    免费：卦名 + 卦象一句 + 总览。
    详批（卦象详解、爻辞、吉凶方位、行动建议）已生成但锁定，需支付 ¥9.9 解锁（未接支付时用 mock_pay 解锁）。
    """
    ch = (body.character or "").strip()
    if not ch:
        raise HTTPException(status_code=400, detail="请输入一个汉字")
    if len(ch) > 1:
        ch = ch[0]

    purpose_code = (body.purpose_code or "").strip() or "fortune"
    purpose_name = PURPOSE_NAMES.get(purpose_code, "问事")

    idx = _hexagram_index(ch, purpose_code)
    hex_name = KW_HEXAGRAM_NAMES[idx]
    brief = _hexagram_brief(hex_name)
    overview = _overview_ai_or_mock(ch, purpose_name, hex_name)
    detail = _mock_detail(ch, purpose_name, hex_name)

    result_id = str(uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _char_sessions[result_id] = {
        "character": ch,
        "purpose_code": purpose_code,
        "purpose_name": purpose_name,
        "hexagram": {"index": idx + 1, "name": hex_name, "brief": brief},
        "overview": overview,
        "detail": detail,
        "unlocked": False,
        "unlock_price_cny": UNLOCK_PRICE_CNY,
        "created_at": created_at,
    }

    return APIResponse(
        code=0,
        msg="ok",
        data={
            "result_id": result_id,
            "character": ch,
            "purpose_code": purpose_code,
            "purpose_name": purpose_name,
            "created_at": created_at,
            "format": "iching",
            "hexagram": {"index": idx + 1, "name": hex_name, "brief": brief},
            "overview": overview,
            "detail_locked": True,
            "unlock_price_cny": UNLOCK_PRICE_CNY,
            "detail_section_titles": {
                "hexagram_comment": "卦象详解",
                "yao_ci": "爻辞",
                "auspicious_direction": "吉凶方位",
                "action_advice": "行动建议",
            },
            # 兼容旧前端：仅总览写入 analysis
            "analysis": overview,
        },
    )


class CharacterUnlockBody(BaseModel):
    result_id: str = ""
    """对接真实支付前：传 true 即视为支付成功并解锁详批（mock）。"""
    mock_pay: bool = False


@router_div.post("/character/unlock", response_model=APIResponse[dict])
def mobile_character_unlock(body: CharacterUnlockBody):
    """支付 ¥9.9 解锁测字详批（当前为 mock：mock_pay=true 即可解锁）。"""
    rid = (body.result_id or "").strip()
    if not rid:
        raise HTTPException(status_code=400, detail="result_id 不能为空")
    row = _char_sessions.get(rid)
    if not row:
        raise HTTPException(status_code=404, detail="测算记录不存在或已过期")
    if row.get("unlocked"):
        return APIResponse(
            code=0,
            msg="ok",
            data={
                "result_id": rid,
                "unlocked": True,
                "detail": row["detail"],
                "hexagram": row["hexagram"],
                "overview": row["overview"],
                "unlock_price_cny": row.get("unlock_price_cny", UNLOCK_PRICE_CNY),
            },
        )
    if not body.mock_pay:
        # 注意：前端 axios 拦截器会把非 0 code 当作错误；此处仍返回 0，用 data 表达待支付
        return APIResponse(
            code=0,
            msg="awaiting_payment",
            data={
                "result_id": rid,
                "unlocked": False,
                "unlock_price_cny": row.get("unlock_price_cny", UNLOCK_PRICE_CNY),
                "payment_required": True,
                "payment_hint": "请接入支付后携带支付凭证调用本接口；开发阶段可传 mock_pay=true 模拟解锁。",
            },
        )
    row["unlocked"] = True
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "result_id": rid,
            "unlocked": True,
            "detail": row["detail"],
            "hexagram": row["hexagram"],
            "overview": row["overview"],
            "unlock_price_cny": row.get("unlock_price_cny", UNLOCK_PRICE_CNY),
            "payment_mock": True,
        },
    )


@router_div.get("/character/result", response_model=APIResponse[dict])
def mobile_character_result(result_id: str = Query(...)):
    """根据 result_id 取回测字结果（已解锁则含详批）。"""
    rid = (result_id or "").strip()
    row = _char_sessions.get(rid)
    if not row:
        raise HTTPException(status_code=404, detail="测算记录不存在或已过期")
    data = {
        "result_id": rid,
        "character": row["character"],
        "purpose_code": row["purpose_code"],
        "purpose_name": row["purpose_name"],
        "created_at": row["created_at"],
        "format": "iching",
        "hexagram": row["hexagram"],
        "overview": row["overview"],
        "detail_locked": not row.get("unlocked"),
        "unlock_price_cny": row.get("unlock_price_cny", UNLOCK_PRICE_CNY),
        "analysis": row["overview"],
    }
    if row.get("unlocked"):
        data["detail"] = row["detail"]
    return APIResponse(code=0, msg="ok", data=data)


@router_div.get("/history/list", response_model=APIResponse[dict])
def mobile_divination_history_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：测字历史"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router_div.get("/history/detail", response_model=APIResponse[dict])
def mobile_divination_history_detail(record_id: str = Query(...)):
    """移动端：测字记录详情"""
    return APIResponse(code=0, msg="ok", data={"record_id": record_id})


# ---------- lottery ----------
@router_lot.get("/purpose/list", response_model=APIResponse[list])
def mobile_lottery_purpose_list():
    """移动端：抽签目的选项"""
    return APIResponse(code=0, msg="ok", data=[{"purpose_code": "fortune", "purpose_name": "问财运"}])


class LotteryDrawBody(BaseModel):
    purpose_code: str = ""


@router_lot.post("/draw", response_model=APIResponse[dict])
def mobile_lottery_draw(body: LotteryDrawBody):
    """移动端：抽签（DeepSeek 生成签文）"""
    sys = "你是解签师。请随机生成一签：签号（如第壹签）、吉凶等级（上上/上吉/中平/下等）、一句签诗、一句白话解释。用中文，一行一行写，格式：签号、等级、签诗、解释。"
    user = f"问事类型：{body.purpose_code or '求签'}"
    text = _call_ai(sys, user)
    lines = [s.strip() for s in (text or "").split("\n") if s.strip()]
    lottery_no = lines[0] if lines else "第壹签"
    lottery_level = lines[1] if len(lines) > 1 else "上上签"
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "lottery_id": str(uuid4()),
            "lottery_no": lottery_no,
            "lottery_level": lottery_level,
            "draw_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "lottery_poetry": lines[2] if len(lines) > 2 else text,
            "lottery_explain": lines[3] if len(lines) > 3 else text,
        },
    )


@router_lot.get("/history/list", response_model=APIResponse[dict])
def mobile_lottery_history_list(page_num: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """移动端：抽签历史"""
    return APIResponse(code=0, msg="ok", data={"total": 0, "list": []})


@router_lot.get("/history/detail", response_model=APIResponse[dict])
def mobile_lottery_history_detail(lottery_id: str = Query(...)):
    """移动端：抽签记录详情"""
    return APIResponse(code=0, msg="ok", data={"lottery_id": lottery_id})


class LotteryInterpretBody(BaseModel):
    lottery_id: str = ""


@router_lot.post("/interpret", response_model=APIResponse[dict])
def mobile_lottery_interpret(body: LotteryInterpretBody):
    """移动端：解签（DeepSeek）"""
    sys = "你是解签师，对用户抽到的签给出签诗与详细白话解释，语气温和、正向。用中文。"
    user = f"签 ID：{body.lottery_id}，请直接给出一段签诗和一段解释。"
    text = _call_ai(sys, user)
    return APIResponse(
        code=0,
        msg="ok",
        data={
            "lottery_id": body.lottery_id,
            "lottery_poetry": text.split("\n")[0] if text else "",
            "lottery_explain": text,
        },
    )


@router_lot.post("/share", response_model=APIResponse[dict])
def mobile_lottery_share(body: LotteryInterpretBody):
    """移动端：分享抽签"""
    return APIResponse(code=0, msg="ok", data={"share_url": "", "share_image": "", "share_title": ""})
