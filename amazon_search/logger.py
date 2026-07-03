"""Logging delle ricerche. Record per debugging e tracking quota."""
import json
import time
from pathlib import Path

LOG_FILE = Path.home() / ".amazon_search_log.jsonl"


def log_search(
    query: str,
    domain: str,
    results_count: int,
    source: str,
    duration_sec: float,
    quota_before: dict,
    quota_after: dict,
    cache_hit: bool = False,
) -> None:
    """Log una ricerca. JSONL format (1 entry per riga)."""
    entry = {
        "timestamp": time.time(),
        "query": query,
        "domain": domain,
        "results": results_count,
        "source": source,  # "serpapi", "searchapi", "cache"
        "duration_s": round(duration_sec, 2),
        "cache_hit": cache_hit,
        "quota": {
            "before": quota_before,
            "after": quota_after,
            "delta": {k: quota_after.get(k, 0) - quota_before.get(k, 0) for k in quota_before},
        },
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠ Log write failed: {e}")


def read_logs(limit: int = 100) -> list[dict]:
    """Read recent log entries."""
    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE) as f:
            entries = [json.loads(line) for line in f.readlines()]
        return entries[-limit:]
    except Exception:
        return []


def summarize_logs() -> dict:
    """Riassunto log per quota tracking."""
    entries = read_logs(limit=10000)
    if not entries:
        return {"total_searches": 0, "cache_hits": 0, "quota_cost": {}}

    quota_cost = {"serpapi": 0, "canopy": 0, "searchapi": 0}
    cache_hits = 0

    for e in entries:
        if e.get("cache_hit"):
            cache_hits += 1
        else:
            source = e.get("source", "")
            if source in quota_cost:
                quota_cost[source] += 1

    return {
        "total_searches": len(entries),
        "cache_hits": cache_hits,
        "quota_cost": quota_cost,
        "avg_duration_s": round(sum(e.get("duration_s", 0) for e in entries) / len(entries), 2) if entries else 0,
    }


def print_summary() -> None:
    """Print nice summary."""
    summary = summarize_logs()
    print(f"""
[Log Summary]
Total ricerche: {summary['total_searches']}
Cache hits: {summary['cache_hits']}
API quota used: {summary['quota_cost']}
Avg durata: {summary['avg_duration_s']}s
""")


def clear_logs() -> None:
    """Delete log file."""
    if LOG_FILE.exists():
        LOG_FILE.unlink()
        print("[Log cleared]")
