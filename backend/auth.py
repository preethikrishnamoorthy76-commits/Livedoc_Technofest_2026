import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from jose import jwt
from passlib.context import CryptContext

from config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from db import get_users_collection

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, tenant_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "tenant_id": tenant_id, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.post("/register", response_model=TokenResponse)
async def register_user(payload: RegisterRequest):
    users = get_users_collection()
    existing = await users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    tenant_id = str(uuid.uuid4())
    password_hash = get_password_hash(payload.password)

    user_doc = {
        "email": payload.email,
        "password_hash": password_hash,
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow(),
    }

    await users.insert_one(user_doc)

    token = create_access_token(subject=payload.email, tenant_id=tenant_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest):
    users = get_users_collection()
    user = await users.find_one({"email": payload.email})

    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    tenant_id = user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is missing tenant_id",
        )

    token = create_access_token(subject=payload.email, tenant_id=tenant_id)
    return TokenResponse(access_token=token)
