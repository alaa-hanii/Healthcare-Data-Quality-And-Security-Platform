from fastapi import APIRouter
from ServicesLayer.PowerBI_service import get_dashboard_info, get_dashboard_status

router = APIRouter()


@router.get("/dashboard")
def get_dashboard():
    """Returns the Power BI dashboard link + metadata for the UI."""
    return get_dashboard_info()


@router.get("/status")
def status():
    """Health-check endpoint, mirrors /dwh/status used by the DWH page."""
    return get_dashboard_status()