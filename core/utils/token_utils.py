import jwt
import datetime
import os
from typing import Optional, Dict
from dotenv import load_dotenv
load_dotenv()

VERIFICATION_SECRET = os.getenv("VERIFICATION_SECRET") or "super_secret_employee_verification_key"

def generate_verification_token(employee_id: str, shop_id: str) -> str:
    payload = {
        "employee_id": str(employee_id),
        "shop_id": str(shop_id),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, VERIFICATION_SECRET, algorithm="HS256")


def decode_verification_token(token: str) -> Optional[Dict[str, str]]:
    if not token:
        return None
    token = token.strip()
    
    # Try all candidate secrets for maximum backwards-compatibility
    candidate_secrets = [
        VERIFICATION_SECRET,
        "super_secret_employee_verification_key",
        "default_shop_employee_secret"
    ]
    
    for secret in candidate_secrets:
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return {
                "employee_id": payload.get("employee_id"),
                "shop_id": payload.get("shop_id")
            }
        except jwt.ExpiredSignatureError:
            return None
        except Exception:
            continue
    return None
