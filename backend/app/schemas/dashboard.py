from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModulePosition(BaseModel):
    """Position and size of a module on the dashboard."""
    module_id: str
    x: int = Field(ge=0, description="Column position (0-indexed)")
    y: int = Field(ge=0, description="Row position (0-indexed)")
    w: int = Field(ge=1, le=12, description="Width in columns (1-12)")
    h: int = Field(ge=1, description="Height in rows")


class DashboardLayoutBase(BaseModel):
    """Base dashboard layout schema."""
    columns: int = Field(default=12, ge=1, le=24)
    row_height: int = Field(default=100, ge=50, le=200)


class DashboardLayoutUpdate(DashboardLayoutBase):
    """Schema for updating dashboard layout."""
    positions: list[ModulePosition] | None = None


class DashboardLayoutResponse(DashboardLayoutBase):
    """Schema for dashboard layout response."""
    id: str
    user_id: str
    positions: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
