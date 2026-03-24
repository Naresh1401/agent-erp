"""Background agent worker – processes queued tasks from Redis."""

from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as redis

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def worker_loop():
    """Main worker loop — listens for agent tasks on Redis queue."""
    r = redis.from_url(settings.redis_url)
    logger.info("Agent worker started, listening for tasks…")

    while True:
        try:
            # BLPOP with 5-second timeout
            result = await r.blpop("agent_tasks", timeout=5)
            if result is None:
                continue

            _, raw = result
            task_data = json.loads(raw)
            logger.info(f"Processing task: {task_data.get('agent_type')} / {task_data.get('task_id')}")

            # Import here to avoid circular deps at module level
            from backend.agents.orchestrator import orchestrator
            from backend.db.database import async_session

            async with async_session() as db:
                result = await orchestrator.dispatch(
                    task_data["agent_type"],
                    task_data.get("input_data", {}),
                    db,
                )
                await db.commit()
                logger.info(f"Task completed: {result.get('status')}")

        except Exception:
            logger.exception("Worker error")
            await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop())
