"""移动端接口 v1：基础配置 /api/config/*"""
from fastapi import APIRouter

from backend.app.schemas.common import APIResponse

router = APIRouter(prefix="/api/config", tags=["Mobile-Config"])


@router.get("/nav", response_model=APIResponse[dict])
def mobile_config_nav():
    """移动端：获取导航菜单"""
    return APIResponse(code=0, msg="ok", data={
        "top_nav": [
            {"menu_id": "1", "name": "首页", "link": "/home"},
            {"menu_id": "2", "name": "祈福", "link": "/blessing"},
            {"menu_id": "3", "name": "开光产品", "link": "/mall"},
            {"menu_id": "4", "name": "专家服务", "link": "/expert"},
            {"menu_id": "5", "name": "AI产品", "link": "/ai"},
            {"menu_id": "6", "name": "玄学文化", "link": "/culture"},
            {"menu_id": "7", "name": "在线教学", "link": "/course"},
            {"menu_id": "8", "name": "祭祀", "link": "/sacrifice"},
            {"menu_id": "9", "name": "个人中心", "link": "/user"},
        ],
        "bottom_nav": [
            {"menu_id": "b1", "name": "产品商城", "link": "/mall"},
            {"menu_id": "b2", "name": "玄学文化", "link": "/culture"},
            {"menu_id": "b3", "name": "专家服务", "link": "/expert"},
            {"menu_id": "b4", "name": "AI测算", "link": "/ai"},
            {"menu_id": "b5", "name": "服务条款", "link": "/terms"},
            {"menu_id": "b6", "name": "隐私协议", "link": "/privacy"},
        ],
    })


@router.get("/footer", response_model=APIResponse[dict])
def mobile_config_footer():
    """移动端：获取底部信息"""
    return APIResponse(code=0, msg="ok", data={
        "site_name": "鲲鹏易道文化商城",
        "slogan": "智运乾坤，易道通达",
        "address": "公司详细地址，精确到门牌号",
        "email": "qiyeyouxiang@163.com",
        "phone": "0000-0000000",
        "copyright": "版权所有：鲲鹏易道文化商城司",
        "icp": "粤ICP备00000000号",
    })
