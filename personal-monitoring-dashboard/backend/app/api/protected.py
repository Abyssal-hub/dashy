from fastapi import APIRouter, Depends
from app.services.auth.deps import get_current_user

router = APIRouter(prefix="/protected", tags=["protected"])


@router.get("/me")
async def me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}
