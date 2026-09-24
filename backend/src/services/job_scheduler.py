"""
Background aggregator loop, attached to the FastAPI lifespan. Runs once shortly after
startup, then every AGGREGATE_EVERY_MINUTES (default 30; 0 turns it off). Needs a
long-running process — the GitHub Actions workflow is a backup trigger for hosts that sleep.
Ported from lib/scheduler.js in moracademy-careers-leaderboard-wiring.
"""
import asyncio

from src.config import settings
from src.services.job_aggregator import run_aggregate

_task: "asyncio.Task | None" = None


async def _loop():
    if settings.aggregate_every_minutes <= 0:
        print("[job_scheduler] disabled (AGGREGATE_EVERY_MINUTES=0)")
        return
    while True:
        try:
            result = await run_aggregate()
            print(f"[job_scheduler] aggregate run: {result}")
        except Exception as e:
            print(f"[job_scheduler] aggregate run failed: {e}")  # never crash the server
        await asyncio.sleep(settings.aggregate_every_minutes * 60)


def start_scheduler():
    global _task
    if _task is not None:
        return  # already running
    if not settings.mongodb_uri:
        print("[job_scheduler] disabled (MONGODB_URI not set)")
        return
    _task = asyncio.create_task(_loop())


def stop_scheduler():
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
