from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ProductCategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: Optional[str] = None
    price: float
    stock: int
    zodiacs: List[str] = []
    is_home_show: bool
    home_section: Optional[str] = None
    main_image: Optional[str] = None

    class Config:
        orm_mode = True


class ProductCreate(BaseModel):
    name: str
    category_id: int
    price: float
    init_stock: int
    zodiacs: List[str] = []
    is_home_show: bool = False
    home_section: Optional[str] = None
    main_image: Optional[str] = None
    detail_images: List[str] = []
    kaiguang_images: List[str] = []
    description_html: Optional[str] = None
    status: str = "on"


class ProductOrderItemOut(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int
    amount: float

    class Config:
        orm_mode = True


class ProductOrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    user_mobile: str
    amount_total: float
    pay_status: str
    ship_status: str
    express_company: Optional[str]
    tracking_no: Optional[str]
    created_at: datetime
    items: List[ProductOrderItemOut] = []

    class Config:
        orm_mode = True

