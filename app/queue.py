import asyncio
from contextlib import asynccontextmanager

from fastapi import HTTPException, status

from app.config import settings
from app.metrics import QUEUE_DEPTH

_semaphore = asyncio.Semaphore(settings.max_concurrency)


@asynccontextmanager
async def gpu_slot():
    """Bounds concurrent requests forwarded to Ollama so one GPU doesn't get
    swamped. Waits up to QUEUE_TIMEOUT_SECONDS for a free slot, then 503s."""
    QUEUE_DEPTH.inc()
    try:
        try:
            await asyncio.wait_for(_semaphore.acquire(), timeout=settings.queue_timeout_seconds)
        except TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gateway busy, timed out waiting for a free inference slot",
            )
    finally:
        QUEUE_DEPTH.dec()

    try:
        yield
    finally:
        _semaphore.release()
