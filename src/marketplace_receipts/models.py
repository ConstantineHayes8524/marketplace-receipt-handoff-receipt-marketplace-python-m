from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class OrderStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class SellerAsset(BaseModel):
    shop_name: str = Field(min_length=1)
    support_email: EmailStr


class BuyerUpdate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1)


class OrderHandoff(BaseModel):
    order_id: str = Field(min_length=1)
    status: OrderStatus
    total_cents: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    seller: SellerAsset
    buyer: BuyerUpdate


class ReceiptResult(BaseModel):
    order_id: str
    action: str
    message_id: str | None = None
