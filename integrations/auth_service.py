import httpx
from icecream import ic
from typing import Optional,List
from pydantic import EmailStr
from fastapi import HTTPException




BASE_AUTH_SERVICE_URL="http://127.0.0.1:8010"


async def get_or_create_user(email:Optional[EmailStr]=None,mobile_number:Optional[str]=None):
    if not email and not mobile_number:
        ic("Please provide atlease any one of the param")
        return False
    

    auth_service_base = f"{BASE_AUTH_SERVICE_URL}/auth"
    user_res = None
    async with httpx.AsyncClient(timeout=10) as client:
        if email:
            try:
                response = await client.get(f"{auth_service_base}/users/by-email/{email}")
                if response.status_code == 200:
                    user_res = response.json()
            except Exception as e:
                ic(f"Auth Service lookup by email failed: {e}")
        
        if not user_res and mobile_number:
            try:
                response = await client.get(f"{auth_service_base}/users/by-mobile/{mobile_number}")
                if response.status_code == 200:
                    user_res = response.json()
            except Exception as e:
                ic(f"Auth Service lookup by mobile failed: {e}")
        
        if not user_res:
            try:
                import uuid
                random_pwd = str(uuid.uuid4())
                create_res = await client.post(
                    f"{auth_service_base}/users",
                    json={
                        "email": email,
                        "mobilenumber": mobile_number or "",
                        "password": random_pwd,
                        "two_factor": False
                    }
                )
                if create_res.status_code == 200:
                    user_res = create_res.json()
                else:
                    ic(f"Auth Service create user failed: {create_res.status_code} {create_res.text}")
                    raise HTTPException(status_code=400, detail=f"Failed to register employee on authentication service: {create_res.text}")
            except Exception as e:
                ic(f"Auth Service user creation exception: {e}")
                if not isinstance(e, HTTPException):
                    raise HTTPException(status_code=500, detail=f"Authentication service communication error: {str(e)}")
                raise e
            
    return user_res