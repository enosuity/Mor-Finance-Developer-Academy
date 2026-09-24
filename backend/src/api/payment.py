"""
Payment callback API — SANDBOX ONLY, test-mode proof of concept.

Takes the payload the checkout button logs (telegramHandle, chosenCountryNode, paymentAmount,
transactionReference) and sets status "subscribed" on that student's profile in a local,
in-memory list. It does NOT verify anything with a payment provider (by design, for this test
phase), so it must never be relied on in production: see settings.allow_mock_payment_callback.
Ported from lib/mock-payments.js in moracademy-careers-leaderboard-wiring.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.config import settings
from src.api.leaderboard import normalise_handle

router = APIRouter()

REFERENCE_RE = re.compile(r"^[A-Za-z0-9._-]{4,100}$")

_profiles: List[Dict[str, Any]] = []


def _guard_mock() -> None:
    if not settings.allow_mock_payment_callback:
        raise HTTPException(
            status_code=403,
            detail={"error": "mock_endpoint_disabled", "detail": "the sandbox payment callback is off in production (set ALLOW_MOCK_PAYMENT_CALLBACK=true to enable it)"},
        )


def _validate_callback(body: Dict[str, Any]) -> Dict[str, Any]:
    details: Dict[str, str] = {}
    telegram_handle = normalise_handle(body.get("telegramHandle"))
    chosen_country_node = str(body.get("chosenCountryNode") or "").strip().upper()
    transaction_reference = str(body.get("transactionReference") or "").strip()
    amount_raw = body.get("paymentAmount")
    if isinstance(amount_raw, str):
        amount_raw = amount_raw.strip()
    try:
        payment_amount = float(amount_raw) if amount_raw not in ("", None) and not isinstance(amount_raw, bool) else float("nan")
    except (TypeError, ValueError):
        payment_amount = float("nan")

    if not telegram_handle:
        details["telegramHandle"] = "expected a Telegram username: 5-32 letters, digits or underscores, starting with a letter"
    if chosen_country_node not in settings.payment_countries:
        details["chosenCountryNode"] = f"expected one of: {', '.join(settings.payment_countries)}"
    if payment_amount != payment_amount or payment_amount <= 0:  # NaN check
        details["paymentAmount"] = "expected a number greater than zero"
    if not REFERENCE_RE.match(transaction_reference):
        details["transactionReference"] = "expected 4-100 characters: letters, digits, dot, dash or underscore"

    if details:
        raise HTTPException(status_code=400, detail={"error": "validation_failed", "details": details})

    return {
        "telegramHandle": telegram_handle,
        "chosenCountryNode": chosen_country_node,
        "paymentAmount": payment_amount,
        "transactionReference": transaction_reference,
    }


def _record_mock_payment(values: Dict[str, Any]) -> Dict[str, Any]:
    existing = next((p for p in _profiles if p["telegramHandle"] == values["telegramHandle"]), None)
    profile = existing or {"telegramHandle": values["telegramHandle"]}
    profile.update(values)
    profile["status"] = "subscribed"
    profile["updatedAt"] = datetime.now(timezone.utc).isoformat()
    if not existing:
        _profiles.append(profile)
    return {**profile}


@router.post("")
async def payment_callback(body: Dict[str, Any]):
    _guard_mock()
    values = _validate_callback(body)
    profile = _record_mock_payment(values)
    return {"status": "subscribed", "profile": profile}


@router.get("")
async def payment_callback_list():
    _guard_mock()
    return [{**p} for p in _profiles]
