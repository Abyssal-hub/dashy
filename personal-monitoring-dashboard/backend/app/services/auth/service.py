import uuid
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from passlib.context import CryptContext
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, RefreshToken

# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    """Hash a refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    """Generate a cryptographically secure refresh token."""
    return secrets.token_urlsafe(32)


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt


def verify_access_token(token: str) -> Optional[str]:
    """Verify a JWT access token and return user_id if valid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        password_hash=hashed_password
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_refresh_token(db: AsyncSession, user_id: str) -> Tuple[str, RefreshToken]:
    """Create a new refresh token for a user."""
    token_str = generate_refresh_token()
    token_hash = hash_token(token_str)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    refresh_token = RefreshToken(
        user_id=uuid.UUID(user_id),
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)
    
    return token_str, refresh_token


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """Verify a refresh token and return it if valid."""
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    """Revoke a refresh token."""
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()
    
    if refresh_token:
        refresh_token.revoked = True
        await db.commit()
        return True
    return False


async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> None:
    """Revoke all refresh tokens for a user (logout from all devices)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == uuid.UUID(user_id),
            RefreshToken.revoked == False
        )
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked = True
    
    await db.commit()
