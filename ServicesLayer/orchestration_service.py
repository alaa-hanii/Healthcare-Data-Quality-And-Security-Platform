"""
ServicesLayer/orchestration_service.py
-----------------------------------------
Business logic for the Orchestration layer: summary metrics, the
calendar grid (with scheduled/upcoming/completed/failed days), and the
"next scheduled run" gap logic between Power BI refresh (07:00) and
the STG→DWH pipeline (08:00).
"""

import calendar as _cal
from datetime import datetime, date, timedelta

from ProcessingLayer.orchestration import (
    insert_event, get_events, get_all_events, get_events_between,
)

# Fixed daily schedule, matches the DAG list shown in the UI
PIPELINE_HOUR = 8   # stg_to_dwh_dag runs daily at 08:00
POWERBI_HOUR = 7    # powerbi_refresh_dag runs daily at 07:00
GAP_MINUTES = (PIPELINE_HOUR - POWERBI_HOUR) * 60


def log_event(layer: str, status: str, message: str = "", duration_seconds: float = None) -> dict:
    return insert_event(layer, status, message, duration_seconds)


def get_summary() -> dict:
    events = get_all_events()
    total = len(events)
    success = len([e for e in events if e["status"] == "success"])
    failed = len([e for e in events if e["status"] == "failed"])
    success_rate = round((success / total) * 100, 1) if total else 0.0

    today_str = date.today().isoformat()
    runs_today = len([e for e in events if e["timestamp"].startswith(today_str)])

    now = datetime.utcnow()
    next_powerbi = now.replace(hour=POWERBI_HOUR, minute=0, second=0, microsecond=0)
    if next_powerbi <= now:
        next_powerbi += timedelta(days=1)

    next_pipeline = now.replace(hour=PIPELINE_HOUR, minute=0, second=0, microsecond=0)
    if next_pipeline <= now:
        next_pipeline += timedelta(days=1)

    return {
        "total_runs": total,
        "success_rate": success_rate,
        "runs_today": runs_today,
        "failed_runs": failed,
        "scheduled": {
            "next_powerbi_refresh": next_powerbi.isoformat(),
            "next_pipeline_run": next_pipeline.isoformat(),
            "gap_minutes": GAP_MINUTES,
        },
    }


def get_recent_events(limit: int = 50) -> list:
    return get_events(limit)


def get_calendar(year: int, month: int) -> dict:
    """
    Builds a day-by-day status grid for the given month:
    - success / failed / running -> derived from logged events that day
    - scheduled_today -> today, if the pipeline hasn't run yet
    - upcoming -> future days
    - none -> past days with no events and not today
    """
    today = date.today()
    _, days_in_month = _cal.monthrange(year, month)

    events = get_all_events()
    # Group events by date (YYYY-MM-DD)
    by_day = {}
    for e in events:
        day_key = e["timestamp"][:10]
        by_day.setdefault(day_key, []).append(e)

    days = []
    for day_num in range(1, days_in_month + 1):
        d = date(year, month, day_num)
        day_key = d.isoformat()
        day_events = by_day.get(day_key, [])

        if d > today:
            status = "upcoming"
        elif d == today:
            if day_events:
                has_failed = any(e["status"] == "failed" for e in day_events)
                has_running = any(e["status"] == "running" for e in day_events)
                status = "failed" if has_failed else ("running" if has_running else "success")
            else:
                status = "scheduled_today"
        else:
            if day_events:
                has_failed = any(e["status"] == "failed" for e in day_events)
                status = "failed" if has_failed else "success"
            else:
                status = "none"

        days.append({
            "day": day_num,
            "date": day_key,
            "status": status,
            "run_count": len(day_events),
        })

    return {"year": year, "month": month, "days": days}
