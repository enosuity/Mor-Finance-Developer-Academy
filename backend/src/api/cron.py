"""
Cron trigger for the job aggregator — for an external scheduler (e.g. GitHub Actions)
to call as a backup to the in-process job_scheduler loop, in case the host sleeps.
Ported from the cronAggregate handler in moracademy-careers-leaderboard-wiring.
"""
import hmac

from fastapi import APIRouter, Header, HTTPException

from src.config import settings
from src.services.job_aggregator import run_aggregate

router = APIRouter()


async def _run(authorization: str):
    if not settings.cron_secret:
        raise HTTPException(status_code=404, detail="not_found")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {settings.cron_secret}"):
        raise HTTPException(status_code=401, detail="unauthorized")
    return await run_aggregate()


@router.get("")
async def cron_aggregate_get(authorization: str = Header(default="")):
    return await _run(authorization)


@router.post("")
async def cron_aggregate_post(authorization: str = Header(default="")):
    return await _run(authorization)
