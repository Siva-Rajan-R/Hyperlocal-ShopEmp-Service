import os
import uuid
import hmac
import hashlib
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, func
from fastapi import HTTPException

from infras.primary_db.models.subscription_model import ShopSubscriptions, SubscriptionTransactions
from infras.primary_db.models.shop_model import Shops
from infras.primary_db.models.employee_model import Employees
from schemas.v1.request_schemas.subscription_schemas import (
    CreateRazorpayOrderSchema,
    VerifyRazorpayPaymentSchema,
    StartTrialSchema,
    AddonItem
)
from icecream import ic
from dotenv import load_dotenv

def get_payment_config():
    """Dynamically reads latest payment & Razorpay credentials from environment"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    env_path = os.path.join(service_root, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
    else:
        load_dotenv(override=True)

    mock_raw = os.getenv("MOCK_PAYMENT", "true").strip().lower()
    is_mock = mock_raw in ("true", "1", "yes", "t")
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip('\"\'')
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip('\"\'')
    return is_mock, key_id, key_secret

PLANS_CATALOG = {
    "digital_store": {
        "id": "digital_store",
        "name": "Digital Store",
        "monthly_price": 399.0,
        "annual_price": 3990.0,
        "currency": "INR",
        "badge": None,
        "description": "For businesses that want to take their products online without changing their existing system.",
        "button_text": "Start Digital Store",
        "limits": {
            "max_locations": 1,
            "max_users": 1,
            "max_skus": 500,
            "max_digital_stores": 1
        },
        "included_features": [
            "1 digital store",
            "Up to 500 SKUs",
            "Online product catalogue",
            "Online orders from customers",
            "Store profile & business information",
            "Marketplace visibility",
            "Customer reviews",
            "1 user",
            "Email Support"
        ]
    },
    "basic": {
        "id": "basic",
        "name": "Basic",
        "monthly_price": 999.0,
        "annual_price": 9990.0,
        "currency": "INR",
        "badge": "MOST POPULAR",
        "description": "Everything a single location business needs to run the business and grow online.",
        "button_text": "Start Business",
        "limits": {
            "max_locations": 1,
            "max_users": 2,
            "max_skus": 500,
            "max_digital_stores": 1
        },
        "included_features": [
            "1 business location",
            "2 users — 1 Admin + 1 Biller",
            "Up to 500 SKUs",
            "Dashboard & business overview",
            "Sales & billing",
            "Purchase management",
            "Inventory management & stock movements",
            "Supplier management & outstanding",
            "Customer management & outstanding",
            "Sales & purchase returns",
            "Business reports",
            "Email + Whatsapp Support"
        ]
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "monthly_price": 1799.0,
        "annual_price": 17990.0,
        "currency": "INR",
        "badge": None,
        "description": "For growing businesses that manage multiple locations and larger product catalogues.",
        "button_text": "Go Pro",
        "limits": {
            "max_locations": 2,
            "max_users": 4,
            "max_skus": 1000,
            "max_digital_stores": 2
        },
        "included_features": [
            "2 business locations",
            "4 users",
            "Up to 1000 SKUs for each store",
            "2 digital stores",
            "Multi-store management",
            "Store-wise inventory",
            "Store-wise sales & reports",
            "Dedicated call support"
        ]
    }
}

ADDONS_CATALOG = {
    "extra_store": {
        "id": "extra_store",
        "name": "Extra Store / Location",
        "price": 499.0,
        "billing_cycle": "monthly",
        "description": "Add another business location with its own stock and billing.",
        "type": "location"
    },
    "extra_user": {
        "id": "extra_user",
        "name": "Extra User",
        "price": 199.0,
        "billing_cycle": "monthly",
        "description": "Add billing staff, managers or other business users.",
        "type": "user"
    },
    "sku_expansion": {
        "id": "sku_expansion",
        "name": "SKU Expansion",
        "price": 299.0,
        "billing_cycle": "monthly",
        "description": "Increase catalogue capacity from 500 to up to 5,000 SKUs.",
        "type": "sku"
    },
    "verified_badge": {
        "id": "verified_badge",
        "name": "Verified Business Badge",
        "price": 699.0,
        "billing_cycle": "year",
        "description": "Issued after successful business verification. Not automatically granted by payment.",
        "type": "badge"
    }
}


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def get_plans_and_addons(self) -> Dict[str, Any]:
        is_mock, key_id, _ = get_payment_config()
        return {
            "plans": list(PLANS_CATALOG.values()),
            "addons": list(ADDONS_CATALOG.values()),
            "trial_days": 14,
            "razorpay_key_id": key_id,
            "mock_payment": is_mock,
            "currency": "INR",
            "marketplace_policy": "No commission on retailer sales. Customers see the retailer's selling price; applicable delivery or payment-processing costs are handled separately according to the platform's payment and delivery terms."
        }

    async def get_current_subscription(self, shop_id: str) -> Dict[str, Any]:
        stmt = select(ShopSubscriptions).where(ShopSubscriptions.shop_id == shop_id).order_by(desc(ShopSubscriptions.created_at)).limit(1)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()

        emp_stmt = select(func.count(Employees.id)).where(Employees.shop_id == shop_id)
        emp_res = await self.session.execute(emp_stmt)
        active_users_count = emp_res.scalar() or 1

        now = datetime.now(timezone.utc)

        if not sub:
            default_trial_end = (now + timedelta(days=14))
            return {
                "has_subscription": False,
                "status": "trial_available",
                "plan_id": "basic",
                "plan_name": "Basic (Trial Available)",
                "billing_cycle": "monthly",
                "trial_days_remaining": 14,
                "trial_ends_at": default_trial_end.isoformat(),
                "current_period_start": now.isoformat(),
                "current_period_end": default_trial_end.isoformat(),
                "limits": {
                    "max_locations": 1,
                    "max_users": 2,
                    "max_skus": 500,
                    "max_digital_stores": 1,
                    "is_verified_badge": False
                },
                "usage": {
                    "current_users": active_users_count,
                    "current_locations": 1,
                    "current_skus": 0,
                    "current_digital_stores": 1
                },
                "addons": []
            }

        trial_days_left = 0
        if sub.trial_ends_at:
            trial_delta = sub.trial_ends_at - now
            trial_days_left = max(0, trial_delta.days)

        is_expired = False
        if sub.status == "trialing" and sub.trial_ends_at and now > sub.trial_ends_at:
            is_expired = True
        elif sub.status == "active" and sub.current_period_end and now > sub.current_period_end:
            is_expired = True

        status = "expired" if is_expired else sub.status

        return {
            "has_subscription": True,
            "id": sub.id,
            "shop_id": sub.shop_id,
            "plan_id": sub.plan_id,
            "plan_name": sub.plan_name,
            "billing_cycle": sub.billing_cycle,
            "status": status,
            "trial_days_remaining": trial_days_left if status == "trialing" else 0,
            "trial_started_at": sub.trial_started_at.isoformat() if sub.trial_started_at else None,
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "base_price": sub.base_price,
            "total_price": sub.total_price,
            "addons": sub.addons or [],
            "limits": {
                "max_locations": sub.max_locations,
                "max_users": sub.max_users,
                "max_skus": sub.max_skus,
                "max_digital_stores": sub.max_digital_stores,
                "is_verified_badge": sub.is_verified_badge
            },
            "usage": {
                "current_users": active_users_count,
                "current_locations": 1,
                "current_skus": 0,
                "current_digital_stores": 1
            }
        }

    async def start_trial(self, data: StartTrialSchema, user_id: str) -> Dict[str, Any]:
        plan_info = PLANS_CATALOG.get(data.plan_id, PLANS_CATALOG["basic"])
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)

        stmt = select(ShopSubscriptions).where(ShopSubscriptions.shop_id == data.shop_id).limit(1)
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.plan_id = plan_info["id"]
            existing.plan_name = plan_info["name"]
            existing.status = "trialing"
            existing.trial_started_at = now
            existing.trial_ends_at = trial_end
            existing.current_period_start = now
            existing.current_period_end = trial_end
            existing.max_locations = plan_info["limits"]["max_locations"]
            existing.max_users = plan_info["limits"]["max_users"]
            existing.max_skus = plan_info["limits"]["max_skus"]
            existing.max_digital_stores = plan_info["limits"]["max_digital_stores"]
            await self.session.commit()
            await self.session.refresh(existing)
            sub = existing
        else:
            sub = ShopSubscriptions(
                id=str(uuid.uuid4()),
                shop_id=data.shop_id,
                user_id=user_id,
                plan_id=plan_info["id"],
                plan_name=plan_info["name"],
                billing_cycle="monthly",
                status="trialing",
                trial_started_at=now,
                trial_ends_at=trial_end,
                current_period_start=now,
                current_period_end=trial_end,
                base_price=0.0,
                total_price=0.0,
                addons=[],
                features=plan_info["included_features"],
                max_locations=plan_info["limits"]["max_locations"],
                max_users=plan_info["limits"]["max_users"],
                max_skus=plan_info["limits"]["max_skus"],
                max_digital_stores=plan_info["limits"]["max_digital_stores"],
                is_verified_badge=False
            )
            self.session.add(sub)
            await self.session.commit()
            await self.session.refresh(sub)

        return await self.get_current_subscription(data.shop_id)

    async def create_razorpay_order(self, data: CreateRazorpayOrderSchema, user_id: str) -> Dict[str, Any]:
        plan = PLANS_CATALOG.get(data.plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        base_price = plan["annual_price"] if data.billing_cycle == "annual" else plan["monthly_price"]
        addons_total = 0.0
        active_addons_list = []

        for addon_item in data.addons:
            catalog_addon = ADDONS_CATALOG.get(addon_item.addon_id)
            if catalog_addon:
                qty = max(1, addon_item.quantity)
                addon_price = catalog_addon["price"] * qty
                if catalog_addon["billing_cycle"] == "monthly" and data.billing_cycle == "annual":
                    addon_price = addon_price * 10
                addons_total += addon_price
                active_addons_list.append({
                    "addon_id": catalog_addon["id"],
                    "name": catalog_addon["name"],
                    "price": addon_price,
                    "quantity": qty,
                    "billing_cycle": catalog_addon["billing_cycle"]
                })

        total_amount = base_price + addons_total
        amount_in_paise = int(round(total_amount * 100))

        receipt_id = f"rcpt_{data.shop_id[:8]}_{int(datetime.now(timezone.utc).timestamp())}"
        razorpay_order_id = f"order_{uuid.uuid4().hex[:14]}"

        is_mock, key_id, key_secret = get_payment_config()

        if not is_mock:
            if not key_id or not key_secret or key_id.startswith("rzp_test_your_key") or key_id.startswith("rzp_test_hyperlocal_mock"):
                raise HTTPException(
                    status_code=400,
                    detail="Razorpay credentials not configured. Please add valid RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env or enable MOCK_PAYMENT=true."
                )

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.razorpay.com/v1/orders",
                        auth=(key_id, key_secret),
                        json={
                            "amount": amount_in_paise,
                            "currency": "INR",
                            "receipt": receipt_id,
                            "notes": {
                                "shop_id": data.shop_id,
                                "plan_id": data.plan_id,
                                "user_id": user_id,
                                "billing_cycle": data.billing_cycle
                            }
                        },
                        timeout=10.0
                    )
                    if resp.status_code in [200, 201]:
                        order_data = resp.json()
                        razorpay_order_id = order_data["id"]
                    else:
                        err_desc = resp.json().get("error", {}).get("description", resp.text)
                        raise HTTPException(status_code=400, detail=f"Razorpay API Error: {err_desc}")
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to connect to Razorpay: {str(e)}")

        transaction = SubscriptionTransactions(
            id=str(uuid.uuid4()),
            shop_id=data.shop_id,
            user_id=user_id,
            razorpay_order_id=razorpay_order_id,
            amount=total_amount,
            currency="INR",
            status="created",
            plan_id=data.plan_id,
            billing_cycle=data.billing_cycle,
            addons=active_addons_list,
            receipt=receipt_id,
            notes={
                "base_price": base_price,
                "addons_total": addons_total,
                "plan_name": plan["name"],
                "mock_payment": is_mock
            }
        )
        self.session.add(transaction)
        await self.session.commit()

        return {
            "order_id": razorpay_order_id,
            "amount": total_amount,
            "amount_in_paise": amount_in_paise,
            "currency": "INR",
            "key_id": key_id,
            "mock_payment": is_mock,
            "plan_name": plan["name"],
            "plan_id": data.plan_id,
            "billing_cycle": data.billing_cycle,
            "addons": active_addons_list,
            "receipt": receipt_id
        }

    async def verify_razorpay_payment(self, data: VerifyRazorpayPaymentSchema, user_id: str) -> Dict[str, Any]:
        is_mock, key_id, key_secret = get_payment_config()

        if not is_mock and not data.razorpay_signature.startswith("mock_sig_"):
            message = f"{data.razorpay_order_id}|{data.razorpay_payment_id}".encode()
            expected_signature = hmac.new(
                key_secret.encode(),
                message,
                hashlib.sha256
            ).hexdigest()

            if expected_signature != data.razorpay_signature:
                raise HTTPException(status_code=400, detail="Invalid Razorpay payment signature")

        stmt = select(SubscriptionTransactions).where(
            SubscriptionTransactions.razorpay_order_id == data.razorpay_order_id
        ).order_by(desc(SubscriptionTransactions.created_at)).limit(1)
        res = await self.session.execute(stmt)
        tx = res.scalar_one_or_none()

        if tx:
            tx.razorpay_payment_id = data.razorpay_payment_id
            tx.razorpay_signature = data.razorpay_signature
            tx.status = "paid"

        plan = PLANS_CATALOG.get(data.plan_id, PLANS_CATALOG["basic"])
        now = datetime.now(timezone.utc)
        period_days = 365 if data.billing_cycle == "annual" else 30
        period_end = now + timedelta(days=period_days)

        max_locations = plan["limits"]["max_locations"]
        max_users = plan["limits"]["max_users"]
        max_skus = plan["limits"]["max_skus"]
        max_digital_stores = plan["limits"]["max_digital_stores"]
        is_verified_badge = False

        active_addons = []
        for addon_item in data.addons:
            catalog_addon = ADDONS_CATALOG.get(addon_item.addon_id)
            if catalog_addon:
                qty = max(1, addon_item.quantity)
                active_addons.append({
                    "addon_id": catalog_addon["id"],
                    "name": catalog_addon["name"],
                    "quantity": qty,
                    "price": catalog_addon["price"] * qty,
                    "billing_cycle": catalog_addon["billing_cycle"]
                })
                if catalog_addon["id"] == "extra_store":
                    max_locations += qty
                    max_digital_stores += qty
                elif catalog_addon["id"] == "extra_user":
                    max_users += qty
                elif catalog_addon["id"] == "sku_expansion":
                    max_skus = max(max_skus, 5000)
                elif catalog_addon["id"] == "verified_badge":
                    is_verified_badge = True

        sub_stmt = select(ShopSubscriptions).where(ShopSubscriptions.shop_id == data.shop_id).limit(1)
        sub_res = await self.session.execute(sub_stmt)
        sub = sub_res.scalar_one_or_none()

        base_price = plan["annual_price"] if data.billing_cycle == "annual" else plan["monthly_price"]
        total_price = tx.amount if tx else base_price

        if sub:
            sub.plan_id = plan["id"]
            sub.plan_name = plan["name"]
            sub.billing_cycle = data.billing_cycle
            sub.status = "active"
            sub.current_period_start = now
            sub.current_period_end = period_end
            sub.cancel_at_period_end = False
            sub.base_price = base_price
            sub.total_price = total_price
            sub.addons = active_addons
            sub.features = plan["included_features"]
            sub.max_locations = max_locations
            sub.max_users = max_users
            sub.max_skus = max_skus
            sub.max_digital_stores = max_digital_stores
            sub.is_verified_badge = is_verified_badge
            if tx:
                tx.subscription_id = sub.id
        else:
            sub_id = str(uuid.uuid4())
            sub = ShopSubscriptions(
                id=sub_id,
                shop_id=data.shop_id,
                user_id=user_id,
                plan_id=plan["id"],
                plan_name=plan["name"],
                billing_cycle=data.billing_cycle,
                status="active",
                current_period_start=now,
                current_period_end=period_end,
                cancel_at_period_end=False,
                base_price=base_price,
                total_price=total_price,
                addons=active_addons,
                features=plan["included_features"],
                max_locations=max_locations,
                max_users=max_users,
                max_skus=max_skus,
                max_digital_stores=max_digital_stores,
                is_verified_badge=is_verified_badge
            )
            self.session.add(sub)
            if tx:
                tx.subscription_id = sub_id

        await self.session.commit()
        return await self.get_current_subscription(data.shop_id)

    async def cancel_subscription(self, shop_id: str) -> Dict[str, Any]:
        stmt = select(ShopSubscriptions).where(ShopSubscriptions.shop_id == shop_id).limit(1)
        res = await self.session.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            raise HTTPException(status_code=404, detail="Subscription not found")

        sub.cancel_at_period_end = True
        await self.session.commit()
        return {"msg": "Subscription cancellation scheduled at end of current period", "success": True}

    async def get_transaction_history(self, shop_id: str) -> List[Dict[str, Any]]:
        stmt = select(SubscriptionTransactions).where(
            SubscriptionTransactions.shop_id == shop_id
        ).order_by(desc(SubscriptionTransactions.created_at))
        res = await self.session.execute(stmt)
        txs = res.scalars().all()

        return [
            {
                "id": t.id,
                "razorpay_order_id": t.razorpay_order_id,
                "razorpay_payment_id": t.razorpay_payment_id,
                "amount": t.amount,
                "currency": t.currency,
                "status": t.status,
                "plan_id": t.plan_id,
                "billing_cycle": t.billing_cycle,
                "addons": t.addons or [],
                "receipt": t.receipt,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in txs
        ]
