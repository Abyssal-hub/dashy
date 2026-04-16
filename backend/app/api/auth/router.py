from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.limiter import limiter, conditional_limit
from app.db.database import get_db_session
from app.schemas.auth import LoginRequest, TokenPair, TokenRefresh
from app.models.user import User
from app.services.auth.service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    verify_refresh_token,
    revoke_refresh_token,
)
from app.services.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
@conditional_limit("3/minute")
async def register(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new user and return access + refresh tokens."""
    from app.services.auth.service import create_user
    
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = await create_user(db, login_data.email, login_data.password)
    
    # Generate tokens
    access_token = create_access_token(str(user.id))
    refresh_token_str, _ = await create_refresh_token(db, str(user.id))
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=settings.environment != "local",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/auth/refresh",
    )
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


@router.post("/login", response_model=TokenPair)
@conditional_limit("5/minute")
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Authenticate user and return access + refresh tokens."""
    user = await authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(str(user.id))
    refresh_token_str, _ = await create_refresh_token(db, str(user.id))
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_str,
        httponly=True,
        secure=settings.environment != "local",  # Secure in production
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/auth/refresh",
    )
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token_str,
    )


@router.post("/refresh", response_model=TokenPair)
@conditional_limit("10/minute")
async def refresh(
    request: Request,
    response: Response,
    token_data: TokenRefresh | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Rotate access token using refresh token."""
    # Prefer body token, fallback to cookie
    token = None
    if token_data and token_data.refresh_token:
        token = token_data.refresh_token
    else:
        token = request.cookies.get("refresh_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )
    
    refresh_token = await verify_refresh_token(db, token)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Issue new tokens
    access_token = create_access_token(str(refresh_token.user_id))
    new_refresh_token_str, _ = await create_refresh_token(db, str(refresh_token.user_id))
    
    # Revoke old refresh token (rotation)
    refresh_token.revoked = True
    await db.commit()
    
    # Update cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token_str,
        httponly=True,
        secure=settings.environment != "local",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/auth/refresh",
    )
    
    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh_token_str,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@conditional_limit("10/minute")
async def logout(
    request: Request,
    response: Response,
    token_data: TokenRefresh | None = None,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Revoke refresh token and clear cookie."""
    if token_data:
        await revoke_refresh_token(db, token_data.refresh_token)
    
    response.delete_cookie(key="refresh_token", path="/auth/refresh")
    return None
