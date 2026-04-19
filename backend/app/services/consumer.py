"""Redis consumer for processing metrics and calendar events from queue.

This module implements an async background consumer that:
- BLPOPs from Redis metrics_queue
- Batches messages (100 messages OR 5s timeout)
- Bulk inserts to TimescaleDB metrics hypertable
- Bulk inserts to calendar_events table
- Handles graceful shutdown and exponential backoff retry
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.handlers.log import write_system_log
from app.db.database import async_session_maker
from app.services.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Queue configuration per ARCHITECTURE.md Section 8.2
QUEUE_NAME = "metrics_queue"
BATCH_SIZE = 100
BATCH_TIMEOUT_SECONDS = 5.0

# Retry configuration with exponential backoff
MAX_RETRIES = 5
BASE_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 60.0  # cap at 1 minute

T = TypeVar("T")


class BatchAccumulator:
    """Accumulates messages in batches for bulk insert."""
    
    def __init__(self, max_size: int = BATCH_SIZE, timeout_seconds: float = BATCH_TIMEOUT_SECONDS):
        self.max_size = max_size
        self.timeout_seconds = timeout_seconds
        self.messages: list[dict[str, Any]] = []
        self._last_flush_time: float | None = None
    
    def add(self, message: dict[str, Any]) -> bool:
        """Add a message to the batch. Returns True if batch should be flushed."""
        self.messages.append(message)
        if self._last_flush_time is None:
            self._last_flush_time = asyncio.get_event_loop().time()
        return len(self.messages) >= self.max_size
    
    def should_flush(self) -> bool:
        """Check if timeout has elapsed."""
        if not self.messages or self._last_flush_time is None:
            return False
        elapsed = asyncio.get_event_loop().time() - self._last_flush_time
        return elapsed >= self.timeout_seconds
    
    def clear(self) -> list[dict[str, Any]]:
        """Clear and return current batch."""
        batch = self.messages
        self.messages = []
        self._last_flush_time = None
        return batch


class RedisConsumer:
    """Async Redis consumer for the metrics queue.
    
    Runs as a background task inside FastAPI lifespan.
    Handles batch accumulation and bulk inserts with retry logic.
    """
    
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._accumulator = BatchAccumulator()
        self._running = False
    
    async def start(self) -> None:
        """Start the consumer as a background task."""
        if self._running:
            logger.warning("Consumer is already running")
            return
        
        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._consume_loop())
        logger.info("Redis consumer started")
        
        # Write system log for consumer start
        try:
            async with async_session_maker() as session:
                await write_system_log(
                    db_session=session,
                    severity="INFO",
                    message="Redis consumer started",
                    source="consumer",
                    metadata={"queue": QUEUE_NAME, "batch_size": BATCH_SIZE},
                )
        except Exception:
            # Don't fail startup if logging fails
            logger.warning("Failed to write system log for consumer start")
    
    async def stop(self) -> None:
        """Gracefully stop the consumer.
        
        Signals shutdown, waits for current batch to complete,
        and cancels the consumer task.
        """
        if not self._running:
            return
        
        logger.info("Initiating consumer shutdown...")
        self._running = False
        self._shutdown_event.set()
        
        if self._task and not self._task.done():
            # Wait for graceful shutdown timeout
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Consumer shutdown timed out, cancelling task")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        # Flush any remaining messages
        if self._accumulator.messages:
            logger.info(f"Flushing remaining {len(self._accumulator.messages)} messages")
            await self._flush_batch(self._accumulator.clear())
        
        logger.info("Redis consumer stopped")
        
        # Write system log for consumer stop
        try:
            async with async_session_maker() as session:
                await write_system_log(
                    db_session=session,
                    severity="INFO",
                    message="Redis consumer stopped gracefully",
                    source="consumer",
                    metadata={"queue": QUEUE_NAME},
                )
        except Exception:
            # Don't fail shutdown if logging fails
            logger.warning("Failed to write system log for consumer stop")
    
    async def _consume_loop(self) -> None:
        """Main consumption loop with BLPOP and batching."""
        redis = get_redis_client()
        
        while self._running:
            try:
                # Try to get a message with BLPOP (blocking with timeout)
                # Use 1 second timeout so we can check for shutdown regularly
                result = await redis.blpop(QUEUE_NAME, timeout=1.0)
                
                if result:
                    # result is a tuple (queue_name, message)
                    _, raw_message = result
                    try:
                        message = json.loads(raw_message)
                        should_flush = self._accumulator.add(message)
                        
                        if should_flush:
                            batch = self._accumulator.clear()
                            await self._flush_batch(batch)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        continue
                
                # Check if timeout-based flush is needed
                if self._accumulator.should_flush():
                    batch = self._accumulator.clear()
                    await self._flush_batch(batch)
                
                # Check for shutdown
                if self._shutdown_event.is_set():
                    break
                    
            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in consumer loop: {e}")
                # Brief pause to prevent tight error loops
                await asyncio.sleep(1.0)
    
    async def _flush_batch(self, batch: list[dict[str, Any]]) -> None:
        """Flush a batch of messages to the database with retry logic."""
        if not batch:
            return
        
        # Separate messages by type
        metrics = [m for m in batch if m.get("type") == "metric"]
        calendar_events = [m for m in batch if m.get("type") == "calendar_event"]
        
        logger.debug(f"Flushing batch: {len(metrics)} metrics, {len(calendar_events)} events")
        
        # Flush with retry logic
        await self._flush_with_retry(
            self._bulk_insert_metrics,
            metrics,
            operation_name="metrics insert"
        )
        
        await self._flush_with_retry(
            self._bulk_insert_calendar_events,
            calendar_events,
            operation_name="calendar_events insert"
        )
    
    async def _flush_with_retry(
        self,
        operation: callable,
        data: list[Any],
        operation_name: str
    ) -> None:
        """Execute an operation with exponential backoff retry."""
        if not data:
            return
        
        for attempt in range(MAX_RETRIES):
            try:
                await operation(data)
                return
            except Exception as e:
                delay = min(BASE_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)
                
                if attempt == MAX_RETRIES - 1:
                    logger.error(
                        f"{operation_name} failed after {MAX_RETRIES} attempts. "
                        f"Dropping {len(data)} records. Error: {e}"
                    )
                    # Write system log for permanent failure
                    try:
                        async with async_session_maker() as session:
                            await write_system_log(
                                db_session=session,
                                severity="ERROR",
                                message=f"{operation_name} failed permanently after {MAX_RETRIES} retries",
                                source="consumer",
                                metadata={
                                    "operation": operation_name,
                                    "records_dropped": len(data),
                                    "error": str(e),
                                    "queue": QUEUE_NAME,
                                },
                            )
                    except Exception:
                        logger.warning("Failed to write system log for consumer error")
                    return
                
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{MAX_RETRIES}). "
                    f"Retrying in {delay}s. Error: {e}"
                )
                await asyncio.sleep(delay)
    
    async def _bulk_insert_metrics(self, metrics: list[dict[str, Any]]) -> None:
        """Bulk insert metrics to TimescaleDB hypertable."""
        if not metrics:
            return
        
        async with async_session_maker() as session:
            # Build bulk insert query
            # TimescaleDB supports standard PostgreSQL bulk inserts
            values = []
            params = {}
            
            for i, metric in enumerate(metrics):
                prefix = f"m{i}"
                values.append(f"(:{prefix}_time, :{prefix}_name, :{prefix}_value, :{prefix}_tags, :{prefix}_source)")
                params[f"{prefix}_time"] = datetime.fromisoformat(metric["timestamp"].replace('Z', '+00:00'))
                params[f"{prefix}_name"] = metric["metric_name"]
                params[f"{prefix}_value"] = metric["value"]
                params[f"{prefix}_tags"] = json.dumps(metric.get("tags", {}))
                params[f"{prefix}_source"] = metric.get("source")
            
            query = text(f"""
                INSERT INTO metrics (time, metric_name, value, tags, source)
                VALUES {','.join(values)}
                ON CONFLICT (time, metric_name) DO UPDATE SET
                    value = EXCLUDED.value,
                    tags = EXCLUDED.tags,
                    source = EXCLUDED.source
            """)
            
            await session.execute(query, params)
            await session.commit()
            
        logger.debug(f"Inserted {len(metrics)} metrics")
    
    async def _bulk_insert_calendar_events(self, events: list[dict[str, Any]]) -> None:
        """Bulk insert calendar events with upsert logic for deduplication."""
        if not events:
            return
        
        async with async_session_maker() as session:
            # Build bulk insert with ON CONFLICT for external_id deduplication
            values = []
            params = {}
            
            for i, event in enumerate(events):
                prefix = f"e{i}"
                # Build value tuple as single line to avoid f-string issues
                val = (
                    f"(:{prefix}_id, :{prefix}_module, :{prefix}_title, :{prefix}_desc, "
                    f":{prefix}_start, :{prefix}_end, :{prefix}_all_day, "
                    f":{prefix}_type, :{prefix}_source, :{prefix}_ext_id, "
                    f":{prefix}_url, :{prefix}_impact, :{prefix}_currency, "
                    f":{prefix}_country, :{prefix}_actual, :{prefix}_forecast, :{prefix}_previous)"
                )
                values.append(val)
                
                # Generate UUID for new events
                import uuid
                params[f"{prefix}_id"] = str(uuid.uuid4())
                
                # Module ID - default to a system module if not provided
                params[f"{prefix}_module"] = event.get("module_id", self._get_default_calendar_module())
                params[f"{prefix}_title"] = event["title"]
                params[f"{prefix}_desc"] = event.get("description", "")
                params[f"{prefix}_start"] = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))
                params[f"{prefix}_end"] = datetime.fromisoformat(event["end_time"].replace('Z', '+00:00')) if event.get("end_time") else None
                params[f"{prefix}_all_day"] = event.get("is_all_day", False)
                params[f"{prefix}_type"] = event.get("event_type", "scraped")
                params[f"{prefix}_source"] = event.get("source", "redis_queue")
                params[f"{prefix}_ext_id"] = event.get("external_id")
                params[f"{prefix}_url"] = event.get("source_url")
                params[f"{prefix}_impact"] = event.get("impact")
                params[f"{prefix}_currency"] = event.get("currency")
                params[f"{prefix}_country"] = event.get("country")
                params[f"{prefix}_actual"] = event.get("actual_value")
                params[f"{prefix}_forecast"] = event.get("forecast_value")
                params[f"{prefix}_previous"] = event.get("previous_value")
            
            query = text(f"""
                INSERT INTO calendar_events (
                    id, module_id, title, description, start_time, end_time, is_all_day,
                    event_type, source, external_id, source_url, impact, currency,
                    country, actual_value, forecast_value, previous_value
                ) VALUES {','.join(values)}
                ON CONFLICT (external_id) WHERE external_id IS NOT NULL DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    start_time = EXCLUDED.start_time,
                    end_time = EXCLUDED.end_time,
                    is_all_day = EXCLUDED.is_all_day,
                    event_type = EXCLUDED.event_type,
                    source = EXCLUDED.source,
                    source_url = EXCLUDED.source_url,
                    impact = EXCLUDED.impact,
                    currency = EXCLUDED.currency,
                    country = EXCLUDED.country,
                    actual_value = EXCLUDED.actual_value,
                    forecast_value = EXCLUDED.forecast_value,
                    previous_value = EXCLUDED.previous_value,
                    updated_at = NOW()
            """)
            
            await session.execute(query, params)
            await session.commit()
            
        logger.debug(f"Inserted {len(events)} calendar events")
    
    def _get_default_calendar_module(self) -> str:
        """Get or create default calendar module ID for scraped events.
        
        In production, this would query the database for the default calendar module.
        For now, returns a placeholder that will need to be configured.
        """
        # This is a placeholder - the actual module ID should be configured
        # or fetched from the database based on the user_id in the message
        # For scraped events without a specific module, they should be associated
        # with the user's default calendar module
        return "00000000-0000-0000-0000-000000000000"


# Global consumer instance
_consumer: RedisConsumer | None = None


def get_consumer() -> RedisConsumer:
    """Get or create the global consumer instance."""
    global _consumer
    if _consumer is None:
        _consumer = RedisConsumer()
    return _consumer


async def start_consumer() -> None:
    """Start the Redis consumer (called from lifespan startup)."""
    consumer = get_consumer()
    await consumer.start()


async def stop_consumer() -> None:
    """Stop the Redis consumer (called from lifespan shutdown)."""
    consumer = get_consumer()
    await consumer.stop()
