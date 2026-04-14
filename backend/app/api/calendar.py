"""Calendar module API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.services.auth.deps import get_current_user
from app.models.calendar import CalendarEvent, CalendarKeywordFilter
from app.models.module import Module
from app.models.user import User
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarEventListResponse,
    CalendarKeywordFilterCreate,
    CalendarKeywordFilterResponse,
    CalendarKeywordFilterListResponse,
)

router = APIRouter(prefix="/modules/{module_id}/calendar", tags=["calendar"])


def _event_to_response(event: CalendarEvent) -> CalendarEventResponse:
    """Convert CalendarEvent model to response schema."""
    return CalendarEventResponse(
        id=event.id,
        module_id=event.module_id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        is_all_day=event.is_all_day,
        event_type=event.event_type,
        source=event.source,
        external_id=event.external_id,
        source_url=event.source_url,
        impact=event.impact,
        currency=event.currency,
        country=event.country,
        actual_value=event.actual_value,
        forecast_value=event.forecast_value,
        previous_value=event.previous_value,
        recurrence_rule=event.recurrence_rule,
        parent_event_id=event.parent_event_id,
        is_active=event.is_active,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


async def _verify_module_access(
    module_id: UUID,
    user: User,
    db_session: AsyncSession,
) -> Module:
    """Verify user has access to the module."""
    result = await db_session.execute(
        select(Module).where(
            and_(
                Module.id == module_id,
                Module.user_id == user.id,
                Module.module_type == "calendar",
                Module.is_active == True,
            )
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar module not found",
        )
    
    return module


@router.get("/events", response_model=CalendarEventListResponse)
async def list_events(
    module_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """List all calendar events for a module."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.module_id == module_id,
                CalendarEvent.is_active == True,
            )
        ).order_by(CalendarEvent.start_time)
    )
    events = result.scalars().all()
    
    return CalendarEventListResponse(
        events=[_event_to_response(e) for e in events],
        total=len(events),
    )


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    module_id: UUID,
    event_data: CalendarEventCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a new personal calendar event."""
    await _verify_module_access(module_id, current_user, db_session)
    
    event = CalendarEvent(
        module_id=module_id,
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        is_all_day=event_data.is_all_day,
        event_type=event_data.event_type,
        source="manual",
        impact=event_data.impact,
        currency=event_data.currency,
        country=event_data.country,
        actual_value=event_data.actual_value,
        forecast_value=event_data.forecast_value,
        previous_value=event_data.previous_value,
        recurrence_rule=event_data.recurrence_rule,
    )
    
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    
    return _event_to_response(event)


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    module_id: UUID,
    event_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Get a specific calendar event."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.id == event_id,
                CalendarEvent.module_id == module_id,
            )
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    return _event_to_response(event)


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    module_id: UUID,
    event_id: UUID,
    event_data: CalendarEventUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Update a calendar event."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.id == event_id,
                CalendarEvent.module_id == module_id,
            )
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    # Update fields
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    await db_session.commit()
    await db_session.refresh(event)
    
    return _event_to_response(event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    module_id: UUID,
    event_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete (soft delete) a calendar event."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarEvent).where(
            and_(
                CalendarEvent.id == event_id,
                CalendarEvent.module_id == module_id,
            )
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    
    event.is_active = False
    await db_session.commit()
    
    return None


# Keyword Filter Endpoints

@router.get("/filters", response_model=CalendarKeywordFilterListResponse)
async def list_keyword_filters(
    module_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """List keyword filters for a calendar module."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarKeywordFilter).where(
            CalendarKeywordFilter.module_id == module_id
        ).order_by(CalendarKeywordFilter.created_at)
    )
    filters = result.scalars().all()
    
    return CalendarKeywordFilterListResponse(
        filters=[
            CalendarKeywordFilterResponse(
                id=f.id,
                module_id=f.module_id,
                keyword=f.keyword,
                is_include=f.is_include,
                created_at=f.created_at,
            )
            for f in filters
        ],
    )


@router.post("/filters", response_model=CalendarKeywordFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword_filter(
    module_id: UUID,
    filter_data: CalendarKeywordFilterCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Create a keyword filter for scraped events."""
    await _verify_module_access(module_id, current_user, db_session)
    
    keyword_filter = CalendarKeywordFilter(
        module_id=module_id,
        keyword=filter_data.keyword,
        is_include=filter_data.is_include,
    )
    
    db_session.add(keyword_filter)
    await db_session.commit()
    await db_session.refresh(keyword_filter)
    
    return CalendarKeywordFilterResponse(
        id=keyword_filter.id,
        module_id=keyword_filter.module_id,
        keyword=keyword_filter.keyword,
        is_include=keyword_filter.is_include,
        created_at=keyword_filter.created_at,
    )


@router.delete("/filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword_filter(
    module_id: UUID,
    filter_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Delete a keyword filter."""
    await _verify_module_access(module_id, current_user, db_session)
    
    result = await db_session.execute(
        select(CalendarKeywordFilter).where(
            and_(
                CalendarKeywordFilter.id == filter_id,
                CalendarKeywordFilter.module_id == module_id,
            )
        )
    )
    keyword_filter = result.scalar_one_or_none()
    
    if not keyword_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter not found",
        )
    
    await db_session.delete(keyword_filter)
    await db_session.commit()
    
    return None
