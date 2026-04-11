import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 使用相对导入，兼容本地 (backend.app.main) 和服务器 (app.main) 两种运行方式
from .api.routers import (
    admin_auth,
    admin_system,
    admin_users,
    admin_products,
    admin_orders,
    captcha,
    dashboard,
    common,
    operation,
    user,
    product,
    product_order,
    blessing,
    sacrifice,
    metaphysics,
    teaching,
    mobile_user,
    mobile_config,
    mobile_ai,
    mobile_content,
    mobile_service,
    mobile_divination,
    mobile_mall,
    mobile_memorial,
    mobile_misc,
)


app = FastAPI(
    title="Kunpeng Yidao Admin & App API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8088", "http://34.87.47.221:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(admin_auth.router)
app.include_router(admin_system.router)
app.include_router(admin_users.router)
app.include_router(admin_products.router)
app.include_router(admin_orders.router)
app.include_router(captcha.router)
app.include_router(dashboard.router)
app.include_router(common.router)
app.include_router(operation.router)
app.include_router(user.router)
app.include_router(product.router)
app.include_router(product_order.router)
app.include_router(blessing.router)
app.include_router(sacrifice.router)
app.include_router(metaphysics.router)
app.include_router(teaching.router)

# 移动端接口 v1（合并到 /docs）
app.include_router(mobile_user.router)
app.include_router(mobile_config.router)
app.include_router(mobile_ai.router)
app.include_router(mobile_content.router)
app.include_router(mobile_service.router)
app.include_router(mobile_divination.router_div)
app.include_router(mobile_divination.router_lot)
app.include_router(mobile_mall.router_mall)
app.include_router(mobile_mall.router_account)
app.include_router(mobile_memorial.router)
app.include_router(mobile_misc.router_fengshui)
app.include_router(mobile_misc.router_dream)
app.include_router(mobile_misc.router_store)
app.include_router(mobile_misc.router_blessing)
app.include_router(mobile_misc.router_naming)
app.include_router(mobile_misc.router_phone)
app.include_router(mobile_misc.router_home)
app.include_router(mobile_misc.router_product)
app.include_router(mobile_misc.router_order)
app.include_router(mobile_misc.router_payment)
app.include_router(mobile_misc.router_cart)
app.include_router(mobile_misc.router_logistics)
app.include_router(mobile_misc.router_region)
app.include_router(mobile_misc.router_metaphysics)
app.include_router(mobile_misc.router_agreement)
app.include_router(mobile_misc.router_auth)
app.include_router(mobile_misc.router_expert)
app.include_router(mobile_misc.router_fortune)

# 上传文件静态访问
_static = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static):
    app.mount("/static", StaticFiles(directory=_static), name="static")


@app.get("/health", tags=["System"])
def health_check() -> dict:
    return {"code": 0, "msg": "ok", "data": {"status": "healthy"}}

