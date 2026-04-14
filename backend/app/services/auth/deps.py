from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.services.auth.service import verify_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> str:
    """Dependency to get the current authenticated user ID from JWT."""
    token = None
    
    # Try Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to query param for WebSocket support
        token = request.query_params.get("token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = verify_access_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str | None:
    """Optional authentication - returns user_id if authenticated, None otherwise."""
    token = None
    
    if credentials:
        token = credentials.credentials
    else:
        token = request.query_params.get("token")
    
    if not token:
        return None
    
    return verify_access_token(token)
