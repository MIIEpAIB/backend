"""DeepSeek API 调用（OpenAI 兼容接口）"""
from openai import OpenAI

from backend.app.core.config import get_settings

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def _client() -> OpenAI:
    settings = get_settings()
    api_key = settings.get_deepseek_api_key()
    if not api_key:
        raise ValueError("DeepSeek API key not configured. Set DEEPSEEK_API_KEY or KUNPENG_DEEPSEEK_API_KEY.")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def chat(system_prompt: str, user_message: str) -> str:
    """调用 DeepSeek 对话，返回助手回复文本。"""
    client = _client()
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=2048,
    )
    if not resp.choices:
        return ""
    return (resp.choices[0].message.content or "").strip()


async def chat_async(system_prompt: str, user_message: str) -> str:
    """异步调用 DeepSeek（当前实现为同步封装，可后续改为 AsyncOpenAI）。"""
    return chat(system_prompt, user_message)
