from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    DECIMAL,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class UserSource(str, Enum):
    portal = "portal"
    backend = "backend"


class AdminUser(Base):
    __tablename__ = "admin_user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(Base):
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mobile = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(64))
    source = Column(SAEnum(UserSource), nullable=False, default=UserSource.portal)
    register_ip = Column(String(64))
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime)
    balance = Column(DECIMAL(12, 2), default=0, nullable=False)
    real_name = Column(String(64))
    status = Column(Integer, default=1, nullable=False)


class UserAddress(Base):
    __tablename__ = "user_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    receiver_name = Column(String(64), nullable=False)
    mobile = Column(String(20), nullable=False)
    province = Column(String(64))
    city = Column(String(64))
    district = Column(String(64))
    detail_addr = Column(String(255))
    is_default = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User")


class ProductCategory(Base):
    __tablename__ = "product_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Product(Base):
    __tablename__ = "product"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    category_id = Column(BigInteger, ForeignKey("product_category.id"), nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)
    init_stock = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    zodiac_flags = Column(String(64))
    is_home_show = Column(Integer, default=0, nullable=False)
    home_section = Column(String(32))
    main_image = Column(String(255))
    description_html = Column(Text)
    status = Column(String(8), default="on", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    category = relationship("ProductCategory")


class ProductOrder(Base):
    __tablename__ = "product_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    address_id = Column(BigInteger, ForeignKey("user_address.id"), nullable=False)
    amount_product = Column(DECIMAL(12, 2), nullable=False)
    amount_shipping = Column(DECIMAL(12, 2), default=0, nullable=False)
    amount_total = Column(DECIMAL(12, 2), nullable=False)
    pay_status = Column(String(16), default="unpaid", nullable=False)
    ship_status = Column(String(16), default="unshipped", nullable=False)
    pay_method = Column(String(16), nullable=False)
    pay_time = Column(DateTime)
    ship_time = Column(DateTime)
    receive_time = Column(DateTime)
    express_company = Column(String(64))
    tracking_no = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User")
    address = relationship("UserAddress")
    items = relationship("ProductOrderItem", back_populates="order")


class ProductOrderItem(Base):
    __tablename__ = "product_order_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("product_order.id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("product.id"), nullable=False)
    product_name = Column(String(128), nullable=False)
    category_name = Column(String(64))
    price = Column(DECIMAL(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)

    order = relationship("ProductOrder", back_populates="items")
    product = relationship("Product")


class BlessItem(Base):
    __tablename__ = "bless_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    price_coin = Column(Integer, nullable=False)
    status = Column(String(8), default="on", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BlessOrder(Base):
    __tablename__ = "bless_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    bless_item_id = Column(BigInteger, ForeignKey("bless_item.id"), nullable=False)
    item_name = Column(String(64), nullable=False)
    price_coin = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_coin = Column(Integer, nullable=False)
    rmb_amount = Column(DECIMAL(12, 2), nullable=False)
    rate_at_order = Column(DECIMAL(12, 4), nullable=False)
    pay_status = Column(String(16), default="unpaid", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime)


class BlessFeed(Base):
    __tablename__ = "bless_feed"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    display_name = Column(String(64), nullable=False)
    bless_item_id = Column(BigInteger, ForeignKey("bless_item.id"))
    bless_item_name = Column(String(64))
    content = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_admin = Column(BigInteger, ForeignKey("admin_user.id"))


class Role(Base):
    __tablename__ = "role"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Permission(Base):
    __tablename__ = "permission"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)

class AdminUserRole(Base):
    __tablename__ = "admin_user_role"

    admin_id = Column(BigInteger, ForeignKey("admin_user.id"), primary_key=True)
    role_id = Column(BigInteger, ForeignKey("role.id"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permission"

    role_id = Column(BigInteger, ForeignKey("role.id"), primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("permission.id"), primary_key=True)


class AdminOpLog(Base):
    __tablename__ = "admin_op_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, ForeignKey("admin_user.id"), nullable=False)
    username = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    target_type = Column(String(64))
    target_id = Column(BigInteger)
    detail = Column(Text)
    ip = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RechargeOrder(Base):
    __tablename__ = "recharge_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    order_no = Column(String(64), unique=True, nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(
        String(16), nullable=False, default="pending"
    )  # pending/success/failed/unknown
    pay_method = Column(String(16), nullable=False)
    channel_txn_id = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    confirmed_by = Column(BigInteger, ForeignKey("admin_user.id"))
    confirmed_at = Column(DateTime)


class BalanceLog(Base):
    __tablename__ = "balance_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    type = Column(String(32), nullable=False)
    amount_change = Column(DECIMAL(12, 2), nullable=False)
    balance_before = Column(DECIMAL(12, 2), nullable=False)
    balance_after = Column(DECIMAL(12, 2), nullable=False)
    ref_type = Column(String(64))
    ref_id = Column(BigInteger)
    remark = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OfferingCategory(Base):
    __tablename__ = "offering_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Offering(Base):
    __tablename__ = "offering"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    category_id = Column(BigInteger, ForeignKey("offering_category.id"))
    icon = Column(String(255))
    price_coin = Column(Integer, nullable=False)
    status = Column(String(8), default="on", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Cemetery(Base):
    __tablename__ = "cemetery"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    deceased_name = Column(String(64), nullable=False)
    gender = Column(String(8), nullable=False)
    birthday = Column(Date)
    death_day = Column(Date)
    epitaph = Column(Text)
    creator_user_id = Column(BigInteger, ForeignKey("user.id"))
    creator_account = Column(String(64))
    relation = Column(String(32))
    avatar_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SacrificeOrder(Base):
    __tablename__ = "sacrifice_order"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)
    cemetery_id = Column(BigInteger, ForeignKey("cemetery.id"))
    deceased_name = Column(String(64))
    relation = Column(String(32))
    offering_id = Column(BigInteger, ForeignKey("offering.id"), nullable=False)
    offering_name = Column(String(64), nullable=False)
    offering_category = Column(String(64))
    price_coin = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_coin = Column(Integer, nullable=False)
    rmb_amount = Column(DECIMAL(12, 2), nullable=False)
    rate_at_order = Column(DECIMAL(12, 4), nullable=False)
    pay_status = Column(String(16), default="unpaid", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime)


class SacrificeFeed(Base):
    __tablename__ = "sacrifice_feed"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.id"))
    user_mobile = Column(String(20))
    offering_name = Column(String(64))
    deceased_name = Column(String(64))
    relation = Column(String(32))
    content = Column(Text)
    sacrifice_time = Column(DateTime, nullable=False)
    created_by_admin = Column(BigInteger, ForeignKey("admin_user.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ArticleCategory(Base):
    __tablename__ = "article_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Article(Base):
    __tablename__ = "article"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category_id = Column(BigInteger, ForeignKey("article_category.id"), nullable=False)
    cover_image = Column(String(255))
    content_html = Column(Text)
    status = Column(String(16), default="draft", nullable=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TeachVideo(Base):
    __tablename__ = "teach_video"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    cover_image = Column(String(255))
    video_url = Column(String(255), nullable=False)
    status = Column(String(8), default="on", nullable=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Courseware(Base):
    __tablename__ = "courseware"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    cover_image = Column(String(255))
    file_url = Column(String(255), nullable=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class One2OneCourse(Base):
    __tablename__ = "one2one_course"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    image = Column(String(255))
    description_html = Column(Text)
    expert_id = Column(BigInteger)
    published_at = Column(DateTime)
    status = Column(String(8), default="on", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LiveEvent(Base):
    __tablename__ = "live_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    live_start = Column(DateTime, nullable=False)
    live_end = Column(DateTime)
    live_url = Column(String(255), nullable=False)
    status = Column(String(16), default="not_started", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ExchangeRate(Base):
    __tablename__ = "exchange_rate"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    currency = Column(String(32), nullable=False)
    rate = Column(DECIMAL(12, 4), nullable=False)
    effective_from = Column(DateTime)
    effective_to = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PayQr(Base):
    __tablename__ = "pay_qr"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pay_method = Column(String(16), nullable=False)
    image_url = Column(String(255), nullable=False)
    status = Column(Integer, default=1, nullable=False)
    remark = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExpertContact(Base):
    __tablename__ = "expert_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    title = Column(String(128))
    avatar_url = Column(String(255))
    mobile = Column(String(20))
    wechat = Column(String(64))
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class HomeBanner(Base):
    __tablename__ = "home_banner"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(128))
    image_url = Column(String(255), nullable=False)
    link_type = Column(String(16), nullable=False)
    link_target = Column(BigInteger)
    link_url = Column(String(255))
    sort_order = Column(Integer, default=0, nullable=False)
    online = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class HomeSection(Base):
    __tablename__ = "home_section"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    key_name = Column(String(64), nullable=False)
    title = Column(String(64), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class HomeSectionProduct(Base):
    __tablename__ = "home_section_product"

    section_id = Column(BigInteger, ForeignKey("home_section.id"), primary_key=True)
    product_id = Column(BigInteger, ForeignKey("product.id"), primary_key=True)
    sort_order = Column(Integer, default=0, nullable=False)


class ContactConfig(Base):
    """专家联系方式配置：按类型存账号列表与开关"""
    __tablename__ = "contact_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_type = Column(String(32), unique=True, nullable=False)
    account_list_json = Column(Text)
    status = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)



