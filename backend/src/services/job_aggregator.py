"""
Job aggregation: fetch every source, keep entry-level jobs, drop duplicates, upsert into
the jobs collection, and prune postings not seen for JOB_TTL_DAYS. A failing source never
stops the others. Ported from lib/careers.js in moracademy-careers-leaderboard-wiring.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings
from src.services.db import get_aggregator_state_collection, get_jobs_collection
from src.services.job_filters import dedupe_keys, is_entry_level
from src.services.job_sources import SOURCES

INTERN_TAGS = {"intern", "internship", "internships", "entry-level", "entry", "junior", "junior-level"}


def _is_intern_tag(t: Any) -> bool:
    return str(t).lower() in INTERN_TAGS


def _job_compat_id(url: str) -> str:
    """Deterministic id from the canonical URL - stable across requests, no extra storage needed."""
    h = 0
    for ch in url:
        h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
    return f"job_{h:0x}"


def _to_compat_job(doc: Dict[str, Any]) -> Dict[str, Any]:
    tags = doc.get("tags") or []
    is_internship = any(_is_intern_tag(t) for t in tags)
    posted_at = doc.get("postedAt")
    return {
        "id": _job_compat_id(doc["url"]),
        "title": doc.get("title"),
        "company": doc.get("company"),
        "location": doc.get("location") or "Remote",
        "remote": bool(doc.get("remote")),
        "salary": "",  # not collected by any source; left blank rather than invented
        "skills": tags,
        "url": doc.get("url"),
        "date": posted_at.isoformat() if posted_at else None,
        "date_epoch": int(posted_at.timestamp()) if posted_at else None,
        "is_internship": is_internship,
        "is_junior": is_internship,
    }


async def list_jobs_compat(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Paginated, filterable job listing: {jobs, page, total_pages, total_jobs}."""
    params = params or {}
    coll = get_jobs_collection()
    cursor = coll.find(
        {}, {"_id": 0, "title": 1, "company": 1, "location": 1, "remote": 1, "url": 1, "postedAt": 1, "tags": 1}
    ).sort("sortAt", -1).limit(2000)

    jobs = [_to_compat_job(doc) async for doc in cursor]

    if params.get("type") == "internships":
        jobs = [j for j in jobs if j["is_internship"]]
    if params.get("remote") is True:
        jobs = [j for j in jobs if j["remote"]]
    if params.get("tag"):
        tag = str(params["tag"]).lower()
        jobs = [j for j in jobs if any(str(s).lower() == tag for s in j["skills"])]
    if params.get("search"):
        q = str(params["search"]).lower()
        jobs = [j for j in jobs if q in " ".join([str(j["title"] or ""), str(j["company"] or ""), *[str(s) for s in j["skills"]]]).lower()]

    total_jobs = len(jobs)
    limit = min(max(int(params.get("limit") or 12), 1), 100)
    total_pages = max(1, -(-total_jobs // limit))  # ceil
    page = min(max(int(params.get("page") or 1), 1), total_pages)
    start = (page - 1) * limit

    return {"jobs": jobs[start:start + limit], "page": page, "total_pages": total_pages, "total_jobs": total_jobs}


async def _acquire_lock(state, now: datetime, ttl_seconds: int = 600) -> bool:
    try:
        res = await state.find_one_and_update(
            {"_id": "aggregate", "$or": [{"until": {"$lt": now}}, {"until": {"$exists": False}}]},
            {"$set": {"until": now + timedelta(seconds=ttl_seconds), "startedAt": now}},
            upsert=True,
            return_document=True,
        )
        return bool(res)
    except Exception as e:
        if "E11000" in str(e):
            return False  # the lock document exists and is still held
        raise


async def run_aggregate() -> Dict[str, Any]:
    state = get_aggregator_state_collection()
    now = datetime.now(timezone.utc)
    if not await _acquire_lock(state, now):
        return {"skipped": "already_running", "ok": True, "sources": [], "added": 0, "updated": 0, "pruned": 0, "total": None}

    try:
        report: List[Dict[str, Any]] = []
        incoming: List[Dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for source in SOURCES:
                try:
                    jobs = await source["fetch"](client)
                    if jobs is None:
                        report.append({"source": source["name"], "status": "skipped", "reason": "not configured"})
                        continue
                    matched = [j for j in jobs if is_entry_level(j)]
                    incoming.extend(matched)
                    report.append({"source": source["name"], "status": "ok", "fetched": len(jobs), "matched": len(matched)})
                except Exception as e:
                    report.append({"source": source["name"], "status": "error", "error": str(e)})

        jobs_coll = get_jobs_collection()
        added = 0
        updated = 0
        for job in incoming:
            keys = dedupe_keys(job)
            posted_at = _parse_date(job.get("postedAt"))
            refresh = {
                "title": job["title"], "company": job["company"], "location": job["location"],
                "remote": job["remote"], "tags": job["tags"], "lastSeenAt": now,
            }

            existing = await jobs_coll.find_one({"keys": {"$in": keys}}, {"_id": 1})
            if existing:
                await jobs_coll.update_one({"_id": existing["_id"]}, {"$set": refresh, "$addToSet": {"keys": {"$each": keys}}})
                updated += 1
                continue
            try:
                await jobs_coll.insert_one({
                    **refresh, "url": job["url"], "source": job["source"], "postedAt": posted_at,
                    "urlKey": keys[0], "keys": keys, "firstSeenAt": now, "sortAt": posted_at or now,
                })
                added += 1
            except Exception as e:
                if "E11000" not in str(e):
                    raise
                raced = await jobs_coll.find_one({"urlKey": keys[0]}, {"_id": 1})  # inserted meanwhile elsewhere
                if raced:
                    await jobs_coll.update_one({"_id": raced["_id"]}, {"$set": refresh, "$addToSet": {"keys": {"$each": keys}}})
                    updated += 1

        cutoff = now - timedelta(days=settings.job_ttl_days)
        prune_res = await jobs_coll.delete_many({"lastSeenAt": {"$lt": cutoff}})
        total = await jobs_coll.count_documents({})
        summary = {
            "sources": report, "added": added, "updated": updated, "pruned": prune_res.deleted_count,
            "total": total, "ok": all(r["status"] != "error" for r in report),
        }
        await state.update_one({"_id": "aggregate"}, {"$set": {"until": datetime.fromtimestamp(0, tz=timezone.utc), "lastRunAt": now, "lastResult": summary}})
        return summary
    except Exception:
        await state.update_one({"_id": "aggregate"}, {"$set": {"until": datetime.fromtimestamp(0, tz=timezone.utc)}})
        raise


def _parse_date(v: Any) -> Optional[datetime]:
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None
