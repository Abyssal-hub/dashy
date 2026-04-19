"""Pydantic schemas for frontend interaction logging."""

from datetime import datetime
from typing import Literal, Any

from pydantic import BaseModel, Field


class InteractionTarget(BaseModel):
    """Target element information for interaction logs."""
    element: str = Field(..., description="DOM element identifier (e.g., 'button', 'input#search')")
    component: str = Field(..., description="React component name")
    route: str = Field(..., description="Current page route (e.g., '/dashboard')")


class InteractionLogCreate(BaseModel):
    """Frontend interaction log entry."""
    interactionId: str = Field(..., description="UUID for correlation between start/end")
    userId: str = Field(..., description="Authenticated user ID")
    sessionId: str = Field(..., description="Browser session identifier")
    type: Literal["click", "hover", "scroll", "input", "navigation", "api_call"] = Field(
        ..., description="Type of user interaction"
    )
    target: InteractionTarget = Field(..., description="Target element/component details")
    metadata: dict[str, Any] | None = Field(None, description="Additional context data")
    startedAt: datetime = Field(..., description="Interaction start time (ISO 8601)")
    endedAt: datetime | None = Field(None, description="Interaction end time (ISO 8601)")
    duration: int | None = Field(None, description="Duration in milliseconds", ge=0)
    success: bool = Field(..., description="Success/failure status")
    error: str | None = Field(None, description="Error message if failed")


class InteractionLogResponse(BaseModel):
    """Response from interaction logging endpoint."""
    status: Literal["logged", "error"] = Field(default="logged")
    message: str = Field(default="Interaction logged successfully")
    interactionId: str | None = None
