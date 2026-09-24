"""
Leaderboard API — testnet activity submissions ranked by distinct transaction count.
Ported from the Node/MongoDB implementation in moracademy-careers-leaderboard-wiring
so leaderboard data lives in the same backend and database as everything else.
"""
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException

from src.config import settings
from src.services.db import get_leaderboard_collection

router = APIRouter()

# Telegram usernames: 5-32 characters, letters/digits/underscore, must start with a letter.
HANDLE_RE = re.compile(r"^[a-z][a-z0-9_]{4,31}$")
TX_HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")

RPC_URLS = {
    "sepolia": settings.rpc_url_sepolia,
    "base-sepolia": settings.rpc_url_base_sepolia,
    "arbitrum-sepolia": settings.rpc_url_arbitrum_sepolia,
    "optimism-sepolia": settings.rpc_url_optimism_sepolia,
}


def normalise_handle(raw: Any) -> Optional[str]:
    """Lower-case handle without '@', or None when it is not a valid Telegram username."""
    handle = str(raw or "").strip().lstrip("@").lower()
    return handle if HANDLE_RE.match(handle) else None


def validate_entry(body: Dict[str, Any]) -> Dict[str, Any]:
    """Returns the cleaned {telegram, chain, txHash}, or raises 400 with per-field errors."""
    errors: Dict[str, str] = {}
    telegram = str(body.get("telegram") or "").strip().lstrip("@").lower()
    chain = str(body.get("chain") or "").strip().lower()
    tx_hash = str(body.get("txHash") or "").strip().lower()

    if not HANDLE_RE.match(telegram):
        errors["telegram"] = "expected a Telegram username: 5-32 letters, digits or underscores, starting with a letter"
    if chain not in settings.chains:
        errors["chain"] = f"expected one of: {', '.join(settings.chains)}"
    if not TX_HASH_RE.match(tx_hash):
        errors["txHash"] = "expected a 0x-prefixed 32-byte transaction hash (66 characters)"

    if errors:
        raise HTTPException(status_code=400, detail={"error": "validation_failed", "details": errors})
    return {"telegram": telegram, "chain": chain, "txHash": tx_hash}


async def verify_onchain(chain: str, tx_hash: str) -> None:
    """Confirms the transaction exists on the chosen testnet and succeeded."""
    rpc = RPC_URLS.get(chain)
    if not rpc:
        raise HTTPException(status_code=503, detail={"error": "verification_unavailable", "detail": f"no RPC configured for {chain}"})
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            res = await client.post(rpc, json={
                "jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash],
            })
            res.raise_for_status()
            body = res.json()
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail={"error": "verification_unavailable", "detail": f"could not reach the {chain} RPC, try again"})

    if body.get("error"):
        raise HTTPException(status_code=503, detail={"error": "verification_unavailable", "detail": f"the {chain} RPC returned an error"})
    result = body.get("result")
    if not result:
        raise HTTPException(status_code=422, detail={"error": "tx_not_found", "detail": f"no such transaction on {chain} (yet)"})
    if result.get("status") != "0x1":
        raise HTTPException(status_code=422, detail={"error": "tx_failed", "detail": "that transaction reverted"})


def rank_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Most distinct transactions first; ties -> more distinct chains; ties -> whoever submitted first."""
    ranked = sorted(
        rows,
        key=lambda r: (-r["txCount"], -r["chainCount"], r["firstSubmittedAt"], r["telegram"]),
    )
    return [
        {"rank": i + 1, "telegram": r["telegram"], "txCount": r["txCount"], "chainCount": r["chainCount"]}
        for i, r in enumerate(ranked)
    ]


async def get_leaderboard() -> List[Dict[str, Any]]:
    coll = get_leaderboard_collection()
    pipeline = [
        {"$group": {
            "_id": "$telegram",
            "txCount": {"$sum": 1},
            "chains": {"$addToSet": "$chain"},
            "firstSubmittedAt": {"$min": "$submittedAt"},
        }}
    ]
    rows = []
    async for r in coll.aggregate(pipeline):
        rows.append({
            "telegram": r["_id"],
            "txCount": r["txCount"],
            "chainCount": len(r["chains"]),
            "firstSubmittedAt": r["firstSubmittedAt"],
        })
    return rank_rows(rows)


@router.get("")
async def leaderboard_get():
    """Ranked leaderboard: rank, telegram, txCount, chainCount."""
    return await get_leaderboard()


@router.post("")
async def leaderboard_post(submission: Dict[str, Any]):
    """Submit a testnet transaction; a tx hash counts once, whoever submits it first."""
    value = validate_entry(submission)

    if settings.verify_onchain:
        await verify_onchain(value["chain"], value["txHash"])

    from datetime import datetime, timezone
    coll = get_leaderboard_collection()
    try:
        await coll.insert_one({**value, "verified": settings.verify_onchain, "submittedAt": datetime.now(timezone.utc)})
    except Exception as e:
        if "E11000" in str(e):
            raise HTTPException(status_code=409, detail={"error": "duplicate_tx", "detail": "this transaction was already submitted"})
        raise

    board = await get_leaderboard()
    rank = next((r["rank"] for r in board if r["telegram"] == value["telegram"]), None)
    return {"telegram": value["telegram"], "rank": rank}
