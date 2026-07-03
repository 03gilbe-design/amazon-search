"""Multi-API quota tracker. Prevents going over free tiers."""
import json
from datetime import datetime
from pathlib import Path

QUOTA_FILE = Path.home() / ".amazon_quota.json"

# Limits: block before hitting paid tier
LIMITS = {
    "serpapi":   {"monthly": True,  "safe": 240, "total": 250},
    "canopy":    {"monthly": True,  "safe": 95,  "total": 100},
    "searchapi": {"monthly": False, "safe": 95,  "total": 100},  # one-time credits
}


def _current_month() -> str:
    return datetime.now().strftime("%Y-%m")


def _load() -> dict:
    if not QUOTA_FILE.exists():
        return {}
    try:
        return json.loads(QUOTA_FILE.read_text())
    except Exception:
        return {}


def _save(data: dict) -> None:
    QUOTA_FILE.write_text(json.dumps(data, indent=2))


def _get_api_state(data: dict, api: str) -> dict:
    month = _current_month()
    cfg = LIMITS[api]

    if api not in data:
        data[api] = {"used": 0, "month": month}
    elif cfg["monthly"] and data[api].get("month") != month:
        # New month → reset
        data[api] = {"used": 0, "month": month}

    return data[api]


def remaining(api: str) -> int:
    data = _load()
    state = _get_api_state(data, api)
    return max(0, LIMITS[api]["safe"] - state["used"])


def used(api: str) -> int:
    data = _load()
    return _get_api_state(data, api)["used"]


def check(api: str) -> bool:
    """Check if API has quota left (does NOT increment)."""
    data = _load()
    state = _get_api_state(data, api)
    return state["used"] < LIMITS[api]["safe"]


def increment(api: str) -> None:
    """Increment usage counter for an API."""
    data = _load()
    state = _get_api_state(data, api)
    state["used"] += 1
    _save(data)


def decrement(api: str) -> None:
    """Roll back an increment (used when API call fails)."""
    data = _load()
    state = _get_api_state(data, api)
    state["used"] = max(0, state["used"] - 1)
    _save(data)


def check_and_increment(api: str) -> bool:
    """Returns True and increments if quota OK. Returns False without touching counter."""
    data = _load()
    state = _get_api_state(data, api)
    if state["used"] >= LIMITS[api]["safe"]:
        return False
    state["used"] += 1
    _save(data)
    return True


def status_all() -> str:
    lines = []
    for api, cfg in LIMITS.items():
        u = used(api)
        r = remaining(api)
        label = "mese" if cfg["monthly"] else "totale"
        lines.append(f"{api}: {u}/{cfg['safe']} usati, {r} rimasti ({label})")
    return "\n".join(lines)


def status_line() -> str:
    parts = []
    for api in LIMITS:
        r = remaining(api)
        parts.append(f"{api}={r}")
    return "Quota rimasta: " + " | ".join(parts)
