"""
ServicesLayer/PowerBI_service.py
----------------------------------
Business-logic layer between ProcessingLayer/PowerBI.py and the
ApplicationLayer endpoint. Mirrors the role of DWH_service.py.
"""

from ProcessingLayer.PowerBI import get_raw_dashboard_url, check_dashboard_reachable


def get_dashboard_info() -> dict:
    """
    Returns the dashboard URL ready to be served by the endpoint,
    along with basic metadata the UI can use.
    """
    url = get_raw_dashboard_url()
    return {
        "dashboard_url": url,
        "source": "DEPI_DWH",
        "schema": "Star Schema (Fact + Dimensions)",
        "access": "ShareLink / Authenticated",
    }


def get_dashboard_status() -> dict:
    """
    Returns connectivity status of the published dashboard link.
    """
    health = check_dashboard_reachable()
    return {
        "dashboard_url": get_raw_dashboard_url(),
        **health,
    }