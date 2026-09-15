from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AddonItem(BaseModel):
    addon_id: str
    quantity: int = 1
    price: Optional[float] = None
    name: Optional[str] = None
    billing_cycle: Optional[str] = "monthly" # 'monthly', 'annual'

class StartTrialSchema(BaseModel):
    shop_id: str
    plan_id: str = "basic"

class CreateRazorpayOrderSchema(BaseModel):
    shop_id: str
    plan_id: str # 'digital_store', 'basic', 'pro'
    billing_cycle: str = "monthly" # 'monthly', 'annual'
    addons: List[AddonItem] = Field(default_factory=list)

class VerifyRazorpayPaymentSchema(BaseModel):
    shop_id: str
    plan_id: str
    billing_cycle: str = "monthly"
    addons: List[AddonItem] = Field(default_factory=list)
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class CancelSubscriptionSchema(BaseModel):
    shop_id: str
    reason: Optional[str] = None
