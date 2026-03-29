from fastapi import Header, HTTPException, Depends
from supabase import create_client, Client
from passlib.context import CryptContext
from pathlib import Path
from dotenv import load_dotenv
import os
import jwt as pyjwt
import logging
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# Supabase
supabase: Client = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_KEY']
)

# Auth
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# AI
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# MongoDB
from pymongo import MongoClient
_mongo_client = MongoClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
mongo_db = _mongo_client[os.environ.get('DB_NAME', 'studiox')]

logger = logging.getLogger("studiox")


def create_token(user_id: str, email: str):
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = supabase.table("users").select("*").eq("id", payload["sub"]).execute()
        if not user.data:
            raise HTTPException(status_code=401, detail="User not found")
        return user.data[0]
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_tenant(user):
    tenant = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant.data:
        raise HTTPException(status_code=404, detail="No tenant found. Create one first.")
    return tenant.data[0]


async def get_current_tenant(user=Depends(get_current_user)):
    """Dependency version: resolves user then gets tenant."""
    return await get_tenant(user)
