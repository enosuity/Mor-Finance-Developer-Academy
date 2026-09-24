"""
Jobs and Careers API — Live integration with Web3.Career API.
Fetches real-time Web3 job listings, internships, and opportunities directly from Web3.Career.
"""
import time
import json
import urllib.request
import urllib.parse
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from src.config import settings

router = APIRouter()

# 5-minute in-memory cache to respect API rate limits while keeping data fresh
_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300

# Mapping common search tags to Web3.Career API recognized slug identifiers
TAG_SLUG_MAP = {
    "go": "golang",
    "golang": "golang",
    "internship": "intern",
    "internships": "intern",
    "intern": "intern",
    "junior": "junior",
    "graduate": "entry-level",
    "apprentice": "entry-level",
    "entry-level": "entry-level",
    "solidity": "solidity",
    "rust": "rust",
    "ai": "ai",
    "ethereum": "ethereum",
    "solana": "solana",
    "polkadot": "polkadot",
    "cosmos": "cosmos",
    "defi": "defi",
    "smart-contracts": "smart-contracts",
    "react": "react",
    "typescript": "typescript",
    "python": "python"
}

def format_salary(job: Dict[str, Any]) -> str:
    """Format salary details into a clean human-readable badge."""
    currency = job.get("salary_currency") or "$"
    if str(currency).upper() == "USD":
        currency = "$"
        
    s_min_raw = job.get("salary_min_value") or job.get("estimated_min_salary")
    s_max_raw = job.get("salary_max_value") or job.get("estimated_max_salary")
    
    try:
        s_min = float(s_min_raw) if s_min_raw is not None else None
    except (ValueError, TypeError):
        s_min = None

    try:
        s_max = float(s_max_raw) if s_max_raw is not None else None
    except (ValueError, TypeError):
        s_max = None
    
    if s_min is not None and s_max is not None and s_max > 0:
        if s_min >= 1000 and s_max >= 1000:
            return f"{currency}{int(s_min // 1000)}k - {currency}{int(s_max // 1000)}k"
        return f"{currency}{int(s_min):,} - {currency}{int(s_max):,}"
    elif s_min is not None and s_min > 0:
        if s_min >= 1000:
            return f"From {currency}{int(s_min // 1000)}k"
        return f"From {currency}{int(s_min):,}"
    elif s_max is not None and s_max > 0:
        if s_max >= 1000:
            return f"Up to {currency}{int(s_max // 1000)}k"
        return f"Up to {currency}{int(s_max):,}"
    
    return "Competitive Web3 Pay"

def fetch_live_web3_career_jobs(
    tag: Optional[str] = None, 
    remote: Optional[bool] = None, 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch live job listings directly from Web3.Career API using the configured API token.
    """
    api_token = settings.web3_career_api_key or "X9q3WrJhceDrdb3oYt2xXeF8Aukh1YsZ"
    
    params: Dict[str, str] = {
        "token": api_token,
        "limit": str(min(100, max(1, limit))),
        "show_description": "false"
    }
    
    if tag and tag.lower() != "all":
        cleaned_tag = tag.lower().strip()
        slug = TAG_SLUG_MAP.get(cleaned_tag, cleaned_tag)
        params["tag"] = slug

    if remote is True:
        params["remote"] = "true"
        
    query_str = urllib.parse.urlencode(params)
    url = f"https://web3.career/api/v1?{query_str}"
    
    # Check in-memory cache
    cache_key = f"{tag}_{remote}_{limit}"
    now = time.time()
    if cache_key in _CACHE:
        entry = _CACHE[cache_key]
        if now - entry["timestamp"] < CACHE_TTL_SECONDS:
            return entry["data"]
            
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail=f"Web3.Career API returned status {response.status}")
                
            raw = json.loads(response.read().decode("utf-8"))
            
            # Web3.Career API format: [header_string, docs_string, [jobs_array]] or direct list
            if isinstance(raw, list):
                if len(raw) > 0 and isinstance(raw[0], dict):
                    raw_jobs = raw
                elif len(raw) > 2 and isinstance(raw[2], list):
                    raw_jobs = raw[2]
                else:
                    raw_jobs = []
            elif isinstance(raw, dict):
                raw_jobs = raw.get("jobs") or raw.get("data") or []
            else:
                raw_jobs = []
            
            formatted: List[Dict[str, Any]] = []
            for idx, item in enumerate(raw_jobs):
                if not isinstance(item, dict):
                    continue
                    
                tags = item.get("tags") or []
                title = (item.get("title") or "").strip()
                company = (item.get("company") or "").strip()
                
                # Split 'Title at Company' if company field was omitted in raw title string
                if not company and " at " in title:
                    parts = title.rsplit(" at ", 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif not company:
                    company = "Web3 Company"

                title_lower = title.lower()
                tags_lower = [t.lower() for t in tags]
                
                is_intern = any(k in title_lower or k in tags_lower for k in ["intern", "internship"])
                is_junior = any(k in title_lower or k in tags_lower for k in ["junior", "graduate", "apprentice", "entry"])
                
                raw_id = item.get("id") or item.get("job_id") or item.get("slug")
                job_id = str(raw_id) if raw_id and str(raw_id).lower() != "none" else f"job-{idx}-{abs(hash(title + company))}"

                formatted.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": (item.get("location") or item.get("city") or item.get("country") or "Remote").strip(),
                    "remote": bool(item.get("is_remote") is True or "remote" in str(item.get("location", "")).lower() or str(item.get("country", "")).lower() == "remote" or remote is True),
                    "country": item.get("country", ""),
                    "city": item.get("city", ""),
                    "salary": format_salary(item),
                    "skills": tags if tags else ["web3", "blockchain"],
                    "url": item.get("apply_url") or "https://web3.career",
                    "date": item.get("date") or "",
                    "date_epoch": item.get("date_epoch") or int(now),
                    "is_internship": is_intern,
                    "is_junior": is_junior or is_intern
                })
                
            if formatted:
                _CACHE[cache_key] = {"data": formatted, "timestamp": now}
            return formatted
            
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("[Web3.Career API] Rate limit reached (429)")
            # If we have any cached data for this key, return it
            if cache_key in _CACHE:
                return _CACHE[cache_key]["data"]
            raise HTTPException(status_code=429, detail="Web3.Career API rate limit reached. Please try again shortly.")
        raise HTTPException(status_code=502, detail=f"Web3.Career upstream HTTP error {e.code}: {e.reason}")
    except Exception as e:
        if cache_key in _CACHE:
            return _CACHE[cache_key]["data"]
        raise HTTPException(status_code=500, detail=f"Failed to fetch live jobs from Web3.Career API: {str(e)}")

import math

@router.get("")
async def get_jobs(
    tag: Optional[str] = Query(None, description="Category filter (solidity, rust, go, ai, internship, remote)"),
    remote: Optional[bool] = Query(None, description="Filter for remote jobs"),
    search: Optional[str] = Query(None, description="Search query string"),
    page: int = Query(1, ge=1, description="Page number (default 1)"),
    limit: int = Query(12, ge=1, le=100, description="Jobs per page (default 12)"),
    type: Optional[str] = Query("all", description="'all' or 'internships'")
):
    """
    Retrieve live Web3 jobs directly from the Web3.Career API feed with multi-page pagination.
    """
    tag_val = tag.strip() if isinstance(tag, str) and tag.strip() and tag.lower() != "all" else None
    
    if isinstance(remote, bool):
        remote_val = remote
    elif isinstance(remote, str):
        remote_val = True if remote.lower() in ("true", "1") else (False if remote.lower() in ("false", "0") else None)
    else:
        remote_val = None

    search_val = search.strip() if isinstance(search, str) and search.strip() else None
    
    try:
        page_val = int(page) if isinstance(page, (int, float)) else (int(page) if isinstance(page, str) and page.isdigit() else 1)
    except (ValueError, TypeError):
        page_val = 1
    page_val = max(1, page_val)

    try:
        limit_val = int(limit) if isinstance(limit, (int, float)) else (int(limit) if isinstance(limit, str) and limit.isdigit() else 12)
    except (ValueError, TypeError):
        limit_val = 12
    limit_val = max(1, min(100, limit_val))
        
    type_val = type.strip().lower() if isinstance(type, str) else "all"

    # If user selected internships, query live API with 'intern' tag
    api_tag = "intern" if (type_val == "internships" and not tag_val) else tag_val

    # Fetch batch of 100 live jobs from Web3.Career API for fast pagination
    live_jobs = fetch_live_web3_career_jobs(tag=api_tag, remote=remote_val, limit=100)
    
    # 1. Filter by internships / entry-level if requested
    if type_val == "internships":
        filtered = [
            j for j in live_jobs
            if j.get("is_internship") or j.get("is_junior") or
            any(kw in j["title"].lower() for kw in ["intern", "junior", "graduate", "apprentice", "entry", "fellowship"])
        ]
    else:
        filtered = list(live_jobs)

    # 2. Filter by search query across title, company, location, and skills
    if search_val:
        q = search_val.lower()
        filtered = [
            j for j in filtered
            if q in j["title"].lower() or 
               q in j["company"].lower() or 
               q in j["location"].lower() or 
               any(q in str(skill).lower() for skill in j.get("skills", []))
        ]

    # 3. Filter by remote if explicitly requested
    if remote_val is True:
        filtered = [j for j in filtered if j.get("remote") is True]

    # Calculate pagination slices
    total_jobs = len(filtered)
    total_pages = max(1, math.ceil(total_jobs / limit_val))
    
    if page_val > total_pages:
        page_val = total_pages
        
    start_idx = (page_val - 1) * limit_val
    end_idx = start_idx + limit_val
    results = filtered[start_idx:end_idx]
    
    return {
        "page": page_val,
        "limit": limit_val,
        "total_jobs": total_jobs,
        "total_pages": total_pages,
        "has_next": page_val < total_pages,
        "has_prev": page_val > 1,
        "count": len(results),
        "total_available": total_jobs,
        "source": "Web3.Career API (Live)",
        "jobs": results
    }
