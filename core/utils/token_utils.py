import jwt
import datetime
import os
from typing import Optional, Dict

VERIFICATION_SECRET = os.getenv("VERIFICATION_SECRET", "default_shop_employee_secret")

def generate_verification_token(employee_id: str, shop_id: str) -> str:
    payload = {
        "employee_id": employee_id,
        "shop_id": shop_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=2)
    }
    return jwt.encode(payload, VERIFICATION_SECRET, algorithm="HS256")

def decode_verification_token(token: str) -> Optional[Dict[str, str]]:
    try:
        payload = jwt.decode(token, VERIFICATION_SECRET, algorithms=["HS256"])
        return {
            "employee_id": payload.get("employee_id"),
            "shop_id": payload.get("shop_id")
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
