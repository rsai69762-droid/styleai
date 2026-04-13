"""Event tracking endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_optional_user_id
from src.db.engine import get_db
from src.db.models import UserEvent
from src.schemas.events import EventBatchIn

router = APIRouter()


@router.post("/events", status_code=202)
async def track_events(
    batch: EventBatchIn,
    user_id=Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Accept a batch of tracking events (anonymous or authenticated)."""
    for event in batch.events:
        db.add(UserEvent(
            user_id=user_id,
            session_id=batch.session_id,
            event_type=event.event_type,
            product_id=event.product_id,
            metadata_=event.metadata,
            duration_ms=event.duration_ms,
        ))
    await db.commit()
    return {"accepted": len(batch.events)}
