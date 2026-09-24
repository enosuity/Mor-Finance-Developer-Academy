"""
Entry-level filter and de-duplication keys for aggregated job postings.
Ported from lib/filters.js in moracademy-careers-leaderboard-wiring.
"""
import hashlib
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# A job is kept only if it looks internship / junior / entry-level AND nothing marks it senior.
# Only the title and the source's own tags are checked - never the description - because descriptions
# routinely say things like "you will work with senior engineers".
INCLUDE_TITLE = re.compile(r"\b(interns?|internships?|junior|jr|entry[\s-]?level)\b", re.IGNORECASE)
INCLUDE_TAGS = {"intern", "internship", "internships", "entry-level", "entry", "junior", "junior-level"}

EXCLUDE_TITLE = re.compile(
    r"\b(senior|sr|staff|principal|lead|head of|director|vp|vice president|chief|cto|ceo|coo|cfo|distinguished)\b",
    re.IGNORECASE,
)
EXCLUDE_TAGS = {"senior", "senior-level", "sr", "lead", "principal", "staff", "director", "executive", "vp", "head"}


def _slug(t: Any) -> str:
    return re.sub(r"\s+", "-", str(t).strip().lower())


def is_entry_level(job: Dict[str, Any]) -> bool:
    title = job.get("title") or ""
    tags = [_slug(t) for t in (job.get("tags") or [])]
    if EXCLUDE_TITLE.search(title) or any(t in EXCLUDE_TAGS for t in tags):
        return False
    return bool(INCLUDE_TITLE.search(title)) or any(t in INCLUDE_TAGS for t in tags)


def _alnum(s: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def canonical_url(raw: Optional[str]) -> str:
    """URL without query, fragment or trailing slash - the same posting always maps to the same key."""
    try:
        u = urlparse(raw)
        if not u.scheme or not u.netloc:
            raise ValueError("not a url")
        return f"{u.netloc.lower()}{u.path.rstrip('/')}"
    except Exception:
        return _alnum(raw)


def dedupe_keys(job: Dict[str, Any]) -> List[str]:
    """Keys identifying a posting: its canonical URL, plus title+company to catch cross-site duplicates."""
    keys = [f"url:{canonical_url(job.get('canonical') or job.get('url'))}"]
    if job.get("company") and job.get("title"):
        keys.append(f"tc:{_alnum(job['title'])}|{_alnum(job['company'])}")
    return keys


def job_id(job: Dict[str, Any]) -> str:
    return hashlib.sha1(canonical_url(job.get("canonical") or job.get("url")).encode()).hexdigest()[:16]
