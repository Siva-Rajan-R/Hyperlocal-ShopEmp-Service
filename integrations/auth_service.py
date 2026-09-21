import httpx
from icecream import ic
from typing import Optional, List
from pydantic import EmailStr
from fastapi import HTTPException
import os
import secrets
import string
from dotenv import load_dotenv
load_dotenv()

BASE_AUTH_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL") or "http://127.0.0.1:8010"


async def get_user_info(email: Optional[EmailStr] = None, mobile_number: Optional[str] = None):
    if not email and not mobile_number:
        return None
    
    auth_service_base = f"{BASE_AUTH_SERVICE_URL}/auth"
    async with httpx.AsyncClient(timeout=10) as client:
        if email:
            try:
                response = await client.get(f"{auth_service_base}/users/by-email/{email}")
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                ic(f"Auth Service lookup by email failed: {e}")
        
        if mobile_number:
            try:
                response = await client.get(f"{auth_service_base}/users/by-mobile/{mobile_number}")
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                ic(f"Auth Service lookup by mobile failed: {e}")
    return None


async def create_user_with_id(
    email: Optional[EmailStr] = None,
    mobile_number: Optional[str] = None,
    user_id: Optional[str] = None,
    password: Optional[str] = None
):
    auth_service_base = f"{BASE_AUTH_SERVICE_URL}/auth"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            if not password:
                # Generate clean secure password e.g. Emp@K9p2m8
                rand_chars = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
                password = f"Emp@{rand_chars}"

            payload = {
                "email": email,
                "mobilenumber": mobile_number or "",
                "password": password,
                "two_factor": False
            }
            if user_id:
                payload["user_id"] = user_id

            create_res = await client.post(
                f"{auth_service_base}/users",
                json=payload
            )
            if create_res.status_code in (200, 201):
                user_res = create_res.json()
                user_res["temp_password"] = password
                return user_res
            else:
                ic(f"Auth Service create user response: {create_res.status_code} {create_res.text}")
                # If user already exists in auth service, return user_id
                if "already exists" in create_res.text.lower():
                    existing = await get_user_info(email=email, mobile_number=mobile_number)
                    if existing:
                        return existing
                return {"user_id": user_id, "temp_password": password}
        except Exception as e:
            ic(f"Auth Service user creation exception: {e}")
            return {"user_id": user_id, "temp_password": password}
