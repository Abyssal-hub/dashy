from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModuleBase(BaseModel):
    """Base module schema."""
    name: str
    config: dict[str, Any]
    size: str = "medium"
    position_x: int = 0
    position_y: int = 0
    width: int | None = None
    height: int | None = None
    refresh_interval: int = 300


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""
    module_type: str


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    name: str | None = None
    config: dict[str, Any] | None = None
    size: str | None = None
    position_x: int | None = None
    position_y: int | None = None
    width: int | None = None
    height: int | None = None
    refresh_interval: int | None = None


class ModuleResponse(BaseModel):
    """Schema for module response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    module_type: str
    name: str
    config: dict[str, Any]
    size: str
    position_x: int
    position_y: int
    width: int | None
    height: int | None
    refresh_interval: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ModuleListResponse(BaseModel):
    """Schema for list of modules response."""
    modules: list[ModuleResponse]
    total: int


class ModuleDataResponse(BaseModel):
    """Schema for module data response."""
    module_id: UUID
    module_type: str
    size: str
    data: dict[str, Any]
