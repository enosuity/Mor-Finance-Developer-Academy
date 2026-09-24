"""
Job sources for the aggregator: CryptoJobsList (RSS) and Web3.Career (API).
Ported from lib/sources.js in moracademy-careers-leaderboard-wiring.

Each source is an async fetch(config, http_client) -> list[dict] | None (None = not configured, skipped).
Each job dict has: source, sourceId, title, company, location, remote, url, canonical, tags, postedAt.
"""
import html
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from src.config import settings

# --- minimal RSS reading (no XML dependency, mirrors the Node implementation) -----------------

_ENTITIES = {"amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'", "nbsp": " "}


def _decode_entities(s: str) -> str:
    def repl(m: "re.Match[str]") -> str:
        e = m.group(1)
        if e.startswith("#"):
            try:
                code = int(e[2:], 16) if e[1:2].lower() == "x" else int(e[1:])
            except ValueError:
                return m.group(0)
            if 0 < code <= 0x10FFFF:
                return chr(code)
            return m.group(0)
        return _ENTITIES.get(e.lower(), m.group(0))

    return re.sub(r"&(#x[0-9a-fA-F]+|#\d+|[a-zA-Z]+);", repl, s)


def _tag_text(block: str, name: str) -> str:
    m = re.search(rf"<{name}(?:\s[^>]*)?>([\s\S]*?)</{name}>", block)
    if not m:
        return ""
    cdata = re.match(r"^\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*$", m.group(1))
    return (cdata.group(1) if cdata else _decode_entities(m.group(1))).strip()


def parse_rss_items(xml: str) -> List[Dict[str, str]]:
    items = []
    for m in re.finditer(r"<item>([\s\S]*?)</item>", xml):
        block = m.group(1)
        description = _tag_text(block, "description")
        block = re.sub(r"<description>[\s\S]*?</description>", "", block, count=1)
        items.append({
            "title": _tag_text(block, "title"),
            "link": _tag_text(block, "link"),
            "canonical": _tag_text(block, "media:canonical"),
            "guid": _tag_text(block, "guid"),
            "creator": _tag_text(block, "dc:creator"),
            "location": re.sub(r"\s+", " ", _tag_text(block, "media:location")).strip(),
            "pubDate": _tag_text(block, "pubDate"),
            "description": description,
        })
    return items


# --- CryptoJobsList (official RSS feed) --------------------------------------------------------

def _cryptojobslist_tags(description_html: str) -> List[str]:
    m = re.search(r"Tags:([\s\S]*?)(?=<b>|</p>|$)", description_html)
    if not m:
        return []
    return [x.lower() for x in re.findall(r'href="https?://cryptojobslist\.com/([a-z0-9-]+)"', m.group(1), re.IGNORECASE)]


def parse_cryptojobslist(xml: str) -> List[Dict[str, Any]]:
    out = []
    for i in parse_rss_items(xml):
        if not i["title"] or not (i["canonical"] or i["link"]):
            continue
        url = i["canonical"] or i["link"]
        tags = _cryptojobslist_tags(i["description"])
        out.append({
            "source": "cryptojobslist",
            "sourceId": i["guid"] or url,
            "title": i["title"],
            "company": i["creator"],
            "location": i["location"],
            "remote": "remote" in tags or bool(re.search(r"remote", i["location"], re.IGNORECASE)),
            "url": url,
            "canonical": url,
            "tags": tags,
            "postedAt": _to_iso(i["pubDate"]),
        })
    return out


async def fetch_cryptojobslist(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    res = await client.get(settings.cryptojobslist_rss_url, headers={"User-Agent": settings.user_agent})
    res.raise_for_status()
    return parse_cryptojobslist(res.text)


# --- Web3.Career (official API, free token) ----------------------------------------------------

def _clean_location(raw: Optional[str]) -> str:
    s = re.sub(r"\s+", " ", str(raw or "")).strip()
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\b((?:\S+\s+){0,3}\S+)\s+\1(?=\s|$)", r"\1", s, flags=re.IGNORECASE)
    return s


def _split_title_and_company(title: str, company: Optional[str]) -> Dict[str, str]:
    if company:
        return {"title": title, "company": str(company)}
    m = re.match(r"^(.*\S)\s+at\s+(\S.*)$", title, re.IGNORECASE)
    if m:
        return {"title": m.group(1), "company": m.group(2)}
    return {"title": title, "company": ""}


def _to_iso(v: Any) -> Optional[str]:
    if not v:
        return None
    for fmt in (None,):
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def parse_web3career(payload: Any, tag: str = "") -> List[Dict[str, Any]]:
    if not isinstance(payload, list):
        raise ValueError("unexpected Web3.Career response format")
    if len(payload) == 0:
        return []
    jobs = next((p for p in payload if isinstance(p, list)), None)
    if jobs is None and isinstance(payload[0], dict):
        jobs = payload
    if jobs is None:
        raise ValueError("could not locate the jobs array in the Web3.Career response")

    out = []
    for j in jobs:
        if not isinstance(j, dict) or not j.get("title") or not (j.get("apply_url") or j.get("url")):
            continue
        tc = _split_title_and_company(str(j["title"]).strip(), j.get("company"))
        location = _clean_location(j.get("location"))
        tags = list(dict.fromkeys(([tag] if tag else []) + [str(t) for t in (j.get("tags") or [])]))
        out.append({
            "source": "web3career",
            "sourceId": str(j.get("id") or j.get("apply_url") or j.get("url")),
            "title": tc["title"],
            "company": tc["company"],
            "location": location,
            "remote": j["remote"] if isinstance(j.get("remote"), bool) else bool(re.search(r"remote", location, re.IGNORECASE)),
            "url": j.get("apply_url") or j.get("url"),
            "canonical": j.get("url") or j.get("apply_url"),
            "tags": tags,
            "postedAt": _to_iso(j.get("postedAt") or j.get("date")),
        })
    return out


async def fetch_web3career(client: httpx.AsyncClient) -> Optional[List[Dict[str, Any]]]:
    if not settings.web3_career_token:
        return None  # not configured -> skipped
    jobs: List[Dict[str, Any]] = []
    errors: List[str] = []
    for tag in settings.web3_career_tags:
        params = {"token": settings.web3_career_token, "tag": tag, "limit": "100", "show_description": "false"}
        try:
            res = await client.get(settings.web3_career_url, params=params, headers={"User-Agent": settings.user_agent})
            res.raise_for_status()
            jobs.extend(parse_web3career(res.json(), tag))
        except Exception as e:
            errors.append(f"tag={tag}: {e}")
    if errors:
        raise RuntimeError("; ".join(errors))  # a partial result is reported as a failed run, not hidden
    return jobs


SOURCES = [
    {"name": "cryptojobslist", "fetch": fetch_cryptojobslist},
    {"name": "web3career", "fetch": fetch_web3career},
]
