from fastapi import APIRouter, Depends, Query, Header, HTTPException
from infras.primary_db.main import get_pg_async_session, AsyncSession
from typing import Annotated, Optional, Dict, Any, List
import json

from schemas.v1.request_schemas.subscription_schemas import (
    CreateRazorpayOrderSchema,
    VerifyRazorpayPaymentSchema,
    StartTrialSchema,
    CancelSubscriptionSchema
)
from infras.primary_db.services.subscription_service import SubscriptionService
from core.utils.user_context import current_user_ctx

router = APIRouter(
    tags=["Subscriptions & Billing"],
    prefix="/shops/subscriptions"
)

direct_router = APIRouter(
    tags=["Subscriptions & Billing"],
    prefix="/subscriptions"
)

PG_ASYNC_SESSION = Annotated[AsyncSession, Depends(get_pg_async_session)]


def get_current_user(x_user_infos: Optional[str] = Header(None, alias="x-user-infos")):
    user_data = current_user_ctx.get()
    if user_data:
        return user_data
    if x_user_infos:
        try:
            return json.loads(x_user_infos)
        except Exception:
            pass
    return {"user_id": "usr_default_owner", "role": "OWNER"}


async def get_plans(session: PG_ASYNC_SESSION):
    """Fetch all available subscription plans and add-ons"""
    service = SubscriptionService(session=session)
    return service.get_plans_and_addons()


async def get_current_subscription(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    """Fetch current subscription, trial status, active add-ons, and limit usage for a shop"""
    service = SubscriptionService(session=session)
    return await service.get_current_subscription(shop_id=shop_id)


async def start_trial(
    data: StartTrialSchema,
    session: PG_ASYNC_SESSION,
    user_info: dict = Depends(get_current_user)
):
    """Start 14-day free trial for a shop (no credit card required)"""
    user_id = user_info.get("user_id", "usr_owner")
    service = SubscriptionService(session=session)
    return await service.start_trial(data=data, user_id=user_id)


async def create_razorpay_order(
    data: CreateRazorpayOrderSchema,
    session: PG_ASYNC_SESSION,
    user_info: dict = Depends(get_current_user)
):
    """Create a Razorpay order for plan upgrade or add-on purchase"""
    user_id = user_info.get("user_id", "usr_owner")
    service = SubscriptionService(session=session)
    return await service.create_razorpay_order(data=data, user_id=user_id)


async def verify_razorpay_payment(
    data: VerifyRazorpayPaymentSchema,
    session: PG_ASYNC_SESSION,
    user_info: dict = Depends(get_current_user)
):
    """Verify Razorpay payment signature and activate/renew subscription"""
    user_id = user_info.get("user_id", "usr_owner")
    service = SubscriptionService(session=session)
    return await service.verify_razorpay_payment(data=data, user_id=user_id)


async def cancel_subscription(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    """Cancel subscription renewal at end of current billing period"""
    service = SubscriptionService(session=session)
    return await service.cancel_subscription(shop_id=shop_id)


async def get_transactions(
    shop_id: str,
    session: PG_ASYNC_SESSION
):
    """Get payment and invoice transaction history for a shop"""
    service = SubscriptionService(session=session)
    return await service.get_transaction_history(shop_id=shop_id)


async def razorpay_webhook(
    payload: Dict[str, Any],
    session: PG_ASYNC_SESSION,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature")
):
    """Handle incoming Razorpay webhooks (e.g. payment.captured, order.paid)"""
    event = payload.get("event")
    return {"status": "received", "event": event}


# Register all endpoints on both router (/shops/subscriptions) and direct_router (/subscriptions)
for r in [router, direct_router]:
    r.add_api_route("/plans", get_plans, methods=["GET"], summary="Get Plans & Add-ons")
    r.add_api_route("/current/{shop_id}", get_current_subscription, methods=["GET"], summary="Get Current Subscription")
    r.add_api_route("/trial/start", start_trial, methods=["POST"], summary="Start 14-day Free Trial")
    r.add_api_route("/razorpay/create-order", create_razorpay_order, methods=["POST"], summary="Create Razorpay Order")
    r.add_api_route("/razorpay/verify-payment", verify_razorpay_payment, methods=["POST"], summary="Verify Payment")
    r.add_api_route("/cancel/{shop_id}", cancel_subscription, methods=["POST"], summary="Cancel Subscription")
    r.add_api_route("/transactions/{shop_id}", get_transactions, methods=["GET"], summary="Get Billing History")
    r.add_api_route("/razorpay/webhook", razorpay_webhook, methods=["POST"], summary="Razorpay Webhook Callback")
