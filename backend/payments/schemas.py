from pydantic import BaseModel
from typing import Optional

class CreateOrderResponse(BaseModel):
    order_id: str
    amount_inr_paise: int # in paise
    currency: str = "INR"

class PassStatusResponse(BaseModel):
    tier: str
    premium_expires_at: Optional[str]