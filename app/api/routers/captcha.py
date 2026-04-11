"""图形验证码 - 免鉴权"""
import base64
import uuid
from fastapi import APIRouter
from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api", tags=["Captcha"])


def _svg_captcha(text: str) -> str:
    """生成简单 SVG 验证码图"""
    w, h = 120, 40
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="100%" height="100%" fill="#f0f0f0"/>',
        f'<text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" font-size="24" fill="#333" font-family="monospace">{text}</text>',
        "</svg>",
    ]
    return "".join(lines)


@router.get("/captcha/image", response_model=APIResponse[dict])
def get_captcha_image():
    """获取图形验证码。登录前调用。"""
    key = str(uuid.uuid4())
    # 简单 4 位数字
    import random
    text = "".join(str(random.randint(0, 9)) for _ in range(4))
    svg = _svg_captcha(text)
    # 实际应在 Redis 等存储 key -> text，校验时比对
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    data = {
        "captcha_key": key,
        "captcha_image": f"data:image/svg+xml;base64,{b64}",
    }
    return APIResponse[dict](code=0, msg="ok", data=data)
