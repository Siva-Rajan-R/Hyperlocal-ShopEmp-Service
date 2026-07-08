import httpx
import jwt
from fastapi import HTTPException
from dotenv import load_dotenv
from core.configs.settings_config import SETTINGS
from icecream import ic


DEBAUTH_BASE_URL="https://api.dauth.debuggers.co.in"

async def get_login_urls():
    constructed_url=f"{DEBAUTH_BASE_URL}/auth"
    urls=requests.post(
        url=constructed_url,
        json={"apikey":SETTINGS.DEB_APIKEY}
    )
    ic(urls.status_code)
    ic(urls.json())
    return urls.json()


async def get_login_urls():
    constructed_url = f"{DEBAUTH_BASE_URL}/auth"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            constructed_url,
            json={
                "apikey": SETTINGS.DEB_APIKEY,
            },
        )

    ic(response.status_code)
    ic(response.json())

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch login URLs",
        )

    return response.json()


async def get_loggedin_user(token_id: str):
    constructed_url = f"{DEBAUTH_BASE_URL}/auth/authenticated-user"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            constructed_url,
            json={
                "token_id": token_id,
                "client_id": SETTINGS.DEB_APIKEY,
                "client_secret": SETTINGS.DEB_SECRETS,
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch authenticated user",
        )

    data = response.json()

    user_infos = jwt.decode(
        data["token"],
        options={"verify_signature": False},  # or verify with your secret/public key
    )

    return user_infos