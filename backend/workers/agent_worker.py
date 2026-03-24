"""Background agent worker entry point."""

from backend.workers import worker_loop
import asyncio
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop())
