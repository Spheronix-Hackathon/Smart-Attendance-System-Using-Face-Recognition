from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from .config import settings
from .database.mongo import get_database
from .schemas import TokenData
from .services.user_service import get_user_by_email, serialize_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_database)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str | None = payload.get("sub")
        if not email:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError as exc:
        raise credentials_exception from exc

    user = await get_user_by_email(db, token_data.email or "")
    if not user:
        raise credentials_exception
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated. Contact admin.")
    return serialize_user(user)


def require_role(*allowed_roles: str):
    async def _dependency(current_user: dict = Depends(get_current_user)) -> dict:
        role = (current_user.get("role") or "student").lower()
        is_admin = bool(current_user.get("is_admin"))
        allowed = {item.lower() for item in allowed_roles}
        if role not in allowed and not (is_admin and "admin" in allowed):
            raise HTTPException(status_code=403, detail="Not authorized")
        return current_user

    return _dependency
