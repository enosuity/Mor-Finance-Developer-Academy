"""
Jobs API — database-backed alternative to jobs.py's live Web3.Career-only fetch.
Combines CryptoJobsList + Web3.Career via a periodic aggregator (see job_scheduler.py
and /api/cron/aggregate) instead of hitting an upstream API on every request.

Mounted at a separate path (/api/jobs-aggregated) rather than replacing the existing
/api/jobs so both can be compared side by side before deciding whether to switch over.
"""
from typing import Optional

from fastapi import APIRouter, Query

from src.services.job_aggregator import list_jobs_compat

router = APIRouter()


@router.get("")
async def get_jobs_aggregated(
    tag: Optional[str] = Query(None),
    remote: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    type: Optional[str] = Query("all", description="'all' or 'internships'"),
):
    """Retrieve entry-level jobs from the aggregated MongoDB store, paginated."""
    return await list_jobs_compat({
        "tag": tag, "remote": remote, "search": search, "page": page, "limit": limit, "type": type,
    })
