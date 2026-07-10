from fastapi import APIRouter
from ServicesLayer.orchestration_service import (
    log_event, get_summary, get_recent_events, get_calendar,
)

router = APIRouter()


@router.post("/log")
def log(layer: str, status: str, message: str = "", duration_seconds: float = None):
    """
    Fire-and-forget logging endpoint called by every layer in the UI
    (ingestion, profiling, quality, security, DWH, Power BI) whenever
    a run finishes — success or failure.
    """
    return log_event(layer, status, message, duration_seconds)


@router.get("/summary")
def summary():
    return get_summary()


@router.get("/events")
def events(limit: int = 50):
    return {"events": get_recent_events(limit)}


@router.get("/calendar")
def calendar(year: int, month: int):
    return get_calendar(year, month)
