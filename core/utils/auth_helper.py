import os
import jwt
import datetime
from typing import Optional, Dict

ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "access_secret_key_12345")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "refresh_secret_key_12345")

def create_access_token(user_id: str, role: str, shop_id: str, gst_registered: bool) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "shop_id": shop_id,
        "gst_registered": gst_registered,
        "token_type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")

def create_refresh_token(user_id: str, role: str, shop_id: str, gst_registered: bool) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "shop_id": shop_id,
        "gst_registered": gst_registered,
        "token_type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, REFRESH_TOKEN_SECRET, algorithm="HS256")

def decode_access_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=["HS256"])
        if payload.get("token_type") == "access":
            return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        pass
    return None

def decode_refresh_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET, algorithms=["HS256"])
        if payload.get("token_type") == "refresh":
            return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        pass
    return None
