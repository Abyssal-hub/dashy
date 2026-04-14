from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.auth.deps import get_current_user
from app.db.database import get_db_session
from app.models.dashboard import DashboardLayout
from app.models.user import User
from app.schemas.dashboard import (
    DashboardLayoutResponse,
    DashboardLayoutUpdate,
    ModulePosition,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _validate_positions(positions: list[ModulePosition]) -> None:
    """Validate that module positions don't overlap."""
    # Simple validation: check for overlapping rectangles
    occupied = set()
    for pos in positions:
        for x in range(pos.x, pos.x + pos.w):
            for y in range(pos.y, pos.y + pos.h):
                if (x, y) in occupied:
                    raise ValueError(f"Position overlap at ({x}, {y})")
                occupied.add((x, y))


@router.get("/layout", response_model=DashboardLayoutResponse)
async def get_dashboard_layout(
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Get the current user's dashboard layout."""
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user_id)
    )
    layout = result.scalar_one_or_none()
    
    if not layout:
        # Create default layout
        layout = DashboardLayout(
            user_id=current_user_id,
            columns=12,
            row_height=100,
            positions=[],
        )
        db.add(layout)
        await db.commit()
        await db.refresh(layout)
    
    return layout


@router.put("/layout", response_model=DashboardLayoutResponse)
async def update_dashboard_layout(
    layout_data: DashboardLayoutUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Update the dashboard layout."""
    # Validate positions
    if layout_data.positions:
        try:
            _validate_positions(layout_data.positions)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user_id)
    )
    layout = result.scalar_one_or_none()
    
    if not layout:
        # Create new layout
        layout = DashboardLayout(
            user_id=current_user_id,
            columns=layout_data.columns or 12,
            row_height=layout_data.row_height or 100,
            positions=[p.model_dump() for p in layout_data.positions] if layout_data.positions else [],
        )
        db.add(layout)
    else:
        # Update existing
        if layout_data.columns is not None:
            layout.columns = layout_data.columns
        if layout_data.row_height is not None:
            layout.row_height = layout_data.row_height
        if layout_data.positions is not None:
            layout.positions = [p.model_dump() for p in layout_data.positions]
    
    await db.commit()
    await db.refresh(layout)
    
    return layout


@router.post("/modules/{module_id}", response_model=DashboardLayoutResponse)
async def add_module_to_dashboard(
    module_id: str,
    position: ModulePosition,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Add a module to the dashboard at the specified position."""
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user_id)
    )
    layout = result.scalar_one_or_none()
    
    if not layout:
        layout = DashboardLayout(
            user_id=current_user_id,
            columns=12,
            row_height=100,
            positions=[],
        )
        db.add(layout)
        await db.flush()
    
    # Check if module already exists
    positions = layout.positions or []
    for i, pos in enumerate(positions):
        if pos.get("module_id") == module_id:
            # Update position
            positions[i] = position.model_dump()
            positions[i]["module_id"] = module_id
            break
    else:
        # Add new position
        pos_dict = position.model_dump()
        pos_dict["module_id"] = module_id
        positions.append(pos_dict)
    
    # Validate no overlap
    try:
        _validate_positions([ModulePosition(**p) for p in positions])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    layout.positions = positions
    await db.commit()
    await db.refresh(layout)
    
    return layout


@router.delete("/modules/{module_id}", response_model=DashboardLayoutResponse)
async def remove_module_from_dashboard(
    module_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Remove a module from the dashboard."""
    result = await db.execute(
        select(DashboardLayout).where(DashboardLayout.user_id == current_user_id)
    )
    layout = result.scalar_one_or_none()
    
    if not layout or not layout.positions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found on dashboard",
        )
    
    # Filter out the module
    original_count = len(layout.positions)
    layout.positions = [p for p in layout.positions if p.get("module_id") != module_id]
    
    if len(layout.positions) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found on dashboard",
        )
    
    await db.commit()
    await db.refresh(layout)
    
    return layout
