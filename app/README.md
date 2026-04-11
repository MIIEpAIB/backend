## 鲲鹏易道商城管理后台（原型 + 后端）

本目录包含：

- Axure 原型导出的前端原型 HTML（管理后台各业务页面）
- 基于 Python + FastAPI + MySQL 的后端接口实现骨架
- 后台功能需求文档 / 接口文档 / 数据库建表脚本

### 目录结构（后端部分）

```text
backend/
  app/
    main.py                 # FastAPI 入口
    core/
      config.py             # 配置（数据库、JWT 等）
      security.py           # 密码加密、Token 生成与解析
    db/
      database.py           # SQLAlchemy Base/Session
      models.py             # 主要数据表的 ORM 模型
    schemas/
      common.py             # 通用响应与分页结构
      admin.py              # 管理员相关 Pydantic 模型
      user.py               # 用户相关 Pydantic 模型
      product.py            # 商品与订单相关 Pydantic 模型
    api/
      routers/
        admin_auth.py       # 管理员登录 / 初始化超级管理员
        admin_users.py      # 后台用户管理接口
        admin_products.py   # 商品分类 / 商品管理接口
        admin_orders.py     # 实物商品订单接口（列表 / 发货）
```

### 配套文档与 SQL

- `后台功能开发完整需求.md`  
  后台每个模块的业务需求说明（功能描述 + 字段要求）。

- `接口文档.md`  
  采用 REST 风格，描述前台 + 后台的主要 HTTP 接口（URL / 请求参数 / 响应示例）。

- `schema.sql`  
  MySQL 建表脚本，包含用户、余额、商品、订单、祈福 / 祭祀、内容、教学、配置等核心表结构。

### 环境准备

1. 安装依赖（建议创建虚拟环境）：

```bash
pip install fastapi uvicorn[standard] SQLAlchemy pymysql python-jose[cryptography] passlib[bcrypt] pydantic-settings
```

2. 初始化数据库：

```bash
mysql -u root -p < schema.sql
```

如需修改数据库连接（用户名 / 密码 / 地址等），在 `backend/app/core/config.py` 中调整默认值，或通过环境变量覆盖：

```bash
set KUNPENG_MYSQL_USER=root
set KUNPENG_MYSQL_PASSWORD=your_password
set KUNPENG_MYSQL_HOST=127.0.0.1
set KUNPENG_MYSQL_DB=kunpeng
```

### 启动后端服务

在本目录下执行：

```bash
uvicorn backend.app.main:app --reload
uvicorn app.main:app --reload
```

启动后可访问：

- 接口文档（Swagger UI）：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

### 初始化超级管理员

首次启动可调用一个开发调试接口创建默认管理员账号（生产环境建议删除或关闭）：

```bash
POST http://localhost:8000/api/admin/init-super-admin
```

成功后默认管理员为：

- 账号：`admin`
- 密码：`admin123`

可用该账号在接口文档中登录并调试后台接口。

### 接下来可以做的事情

- 根据 `接口文档.md` 继续补全剩余模块的路由（祈福 / 祭祀 / 文章 / 教学等）。
- 结合前端正式管理后台项目对接这些接口（当前 HTML 为原型预览，不是正式前端代码）。 

