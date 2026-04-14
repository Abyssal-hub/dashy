from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth.deps import get_current_user
from app.db.database import get_db_session
from app.models.module import Module
from app.modules import get_handler, list_module_types
from app.schemas.module import (
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
    ModuleListResponse,
    ModuleDataResponse,
)

router = APIRouter(prefix="/modules", tags=["modules"])


@router.post("", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    module_data: ModuleCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Create a new module for the current user."""
    # Validate module type exists
    handler_class = get_handler(module_data.module_type)
    if not handler_class:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid module type: {module_data.module_type}",
        )
    
    # Validate config
    handler = handler_class()
    if not handler.validate_config(module_data.config):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module configuration",
        )
    
    # Create module
    module = Module(
        user_id=user_id,
        module_type=module_data.module_type,
        name=module_data.name,
        config=module_data.config,
        size=module_data.size,
        position_x=module_data.position_x,
        position_y=module_data.position_y,
        width=module_data.width,
        height=module_data.height,
        refresh_interval=module_data.refresh_interval,
    )
    
    db.add(module)
    await db.commit()
    await db.refresh(module)
    
    return module


@router.get("", response_model=ModuleListResponse)
async def list_modules(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> Any:
    """List all modules for the current user."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Module).where(Module.user_id == user_id, Module.is_active == True)
    )
    modules = result.scalars().all()
    
    return {"modules": modules, "total": len(modules)}


@router.get("/types")
async def get_module_types() -> dict[str, list[str]]:
    """List available module types."""
    return {"types": list_module_types()}


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Get a specific module by ID."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Module).where(
            Module.id == module_id,
            Module.user_id == user_id,
            Module.is_active == True,
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    
    return module


@router.put("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: UUID,
    module_data: ModuleUpdate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Update a module."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Module).where(
            Module.id == module_id,
            Module.user_id == user_id,
            Module.is_active == True,
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    
    # Validate new config if provided
    if module_data.config is not None:
        handler_class = get_handler(module.module_type)
        if handler_class:
            handler = handler_class()
            if not handler.validate_config(module_data.config):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid module configuration",
                )
        module.config = module_data.config
    
    # Update other fields
    for field, value in module_data.model_dump(exclude_unset=True).items():
        if field != "config":  # Already handled above
            setattr(module, field, value)
    
    await db.commit()
    await db.refresh(module)
    
    return module


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> None:
    """Soft delete a module."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Module).where(
            Module.id == module_id,
            Module.user_id == user_id,
            Module.is_active == True,
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    
    module.is_active = False
    await db.commit()


@router.get("/{module_id}/data", response_model=ModuleDataResponse)
async def get_module_data(
    module_id: UUID,
    size: str | None = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user),
) -> Any:
    """Get data for a module from its handler."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Module).where(
            Module.id == module_id,
            Module.user_id == user_id,
            Module.is_active == True,
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    
    # Get handler
    handler_class = get_handler(module.module_type)
    if not handler_class:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Handler not found for module type: {module.module_type}",
        )
    
    handler = handler_class()
    data_size = size or module.size
    
    data = await handler.get_data(str(module_id), data_size)
    
    return {
        "module_id": module_id,
        "module_type": module.module_type,
        "size": data_size,
        "data": data,
    }
