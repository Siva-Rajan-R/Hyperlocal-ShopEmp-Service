from ..main import BASE
from sqlalchemy import Column, String, ForeignKey, Integer, TIMESTAMP, func, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB

class ShopSubscriptions(BASE):
    __tablename__ = "shop_subscriptions"

    id = Column(String, primary_key=True)
    shop_id = Column(String, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    plan_id = Column(String, nullable=False) # 'digital_store', 'basic', 'pro'
    plan_name = Column(String, nullable=False)
    billing_cycle = Column(String, nullable=False, default="monthly") # 'monthly', 'annual'
    status = Column(String, nullable=False, default="trialing") # 'trialing', 'active', 'past_due', 'cancelled', 'expired'
    
    trial_started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    trial_ends_at = Column(TIMESTAMP(timezone=True), nullable=True)
    current_period_start = Column(TIMESTAMP(timezone=True), nullable=True)
    current_period_end = Column(TIMESTAMP(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    
    base_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    
    addons = Column(JSONB, nullable=True, default=list) # List of active add-ons
    features = Column(JSONB, nullable=True, default=dict)
    
    max_locations = Column(Integer, nullable=False, default=1)
    max_users = Column(Integer, nullable=False, default=1)
    max_skus = Column(Integer, nullable=False, default=500)
    max_digital_stores = Column(Integer, nullable=False, default=1)
    is_verified_badge = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class SubscriptionTransactions(BASE):
    __tablename__ = "subscription_transactions"

    id = Column(String, primary_key=True)
    shop_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    subscription_id = Column(String, nullable=True, index=True)
    
    razorpay_order_id = Column(String, nullable=False, index=True)
    razorpay_payment_id = Column(String, nullable=True, index=True)
    razorpay_signature = Column(String, nullable=True)
    
    amount = Column(Float, nullable=False) # In INR
    currency = Column(String, nullable=False, default="INR")
    status = Column(String, nullable=False, default="created") # 'created', 'paid', 'failed'
    
    plan_id = Column(String, nullable=False)
    billing_cycle = Column(String, nullable=False, default="monthly")
    addons = Column(JSONB, nullable=True, default=list)
    
    receipt = Column(String, nullable=True)
    notes = Column(JSONB, nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
