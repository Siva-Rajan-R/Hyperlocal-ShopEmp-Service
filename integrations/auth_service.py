import httpx
from icecream import ic
from typing import Optional,List
from pydantic import EmailStr
from fastapi import HTTPException
import os
from dotenv import load_dotenv
load_dotenv()




# BASE_AUTH_SERVICE_URL="http://127.0.0.1:8010"
BASE_AUTH_SERVICE_URL= os.getenv("AUTHENTICATION_SERVICE_URL")


async def get_user_info(email:Optional[EmailStr]=None,mobile_number:Optional[str]=None):
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

async def create_user_with_id(email:Optional[EmailStr]=None,mobile_number:Optional[str]=None, user_id:Optional[str]=None):
    auth_service_base = f"{BASE_AUTH_SERVICE_URL}/auth"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            import uuid
            random_pwd = str(uuid.uuid4())
            payload = {
                "email": email,
                "mobilenumber": mobile_number or "",
                "password": random_pwd,
                "two_factor": False
            }
            if user_id:
                payload["user_id"] = user_id
            create_res = await client.post(
                f"{auth_service_base}/users",
                json=payload
            )
            if create_res.status_code == 200:
                user_res = create_res.json()
                user_res["temp_password"] = random_pwd
                return user_res
            else:
                ic(f"Auth Service create user failed: {create_res.status_code} {create_res.text}")
                raise HTTPException(status_code=400, detail=f"Failed to register employee on authentication service: {create_res.text}")
        except Exception as e:
            ic(f"Auth Service user creation exception: {e}")
            if not isinstance(e, HTTPException):
                raise HTTPException(status_code=500, detail=f"Authentication service communication error: {str(e)}")
            raise e