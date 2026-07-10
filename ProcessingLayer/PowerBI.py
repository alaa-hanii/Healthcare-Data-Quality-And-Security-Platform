"""
ProcessingLayer/PowerBI.py
---------------------------
Lowest layer in the Power BI pipeline. Responsible for holding the raw
dashboard source (the published Power BI link) and validating that it's
reachable, the same role the SSIS .dtsx files play for the DWH layer.
"""

import requests

# المصدر الخام - نفس فكرة الـ .dtsx بتاعة الـ DWH بس هنا هو لينك بدل باكدج
DASHBOARD_URL = "https://app.powerbi.com/links/sVc9YDh19Z?ctid=a2c31985-cc3b-4e19-8fa2-59fa488f0c27&pbi_source=linkShare"


def get_raw_dashboard_url() -> str:
    """Returns the raw published Power BI link."""
    return DASHBOARD_URL


def check_dashboard_reachable(timeout: int = 5) -> dict:
    """
    Lightweight health-check on the dashboard URL.
    Power BI share links typically respond even without full auth,
    so we just check that the host responds (HEAD/GET) without raising.
    """
    try:
        resp = requests.get(DASHBOARD_URL, timeout=timeout, allow_redirects=True)
        return {
            "reachable": resp.status_code < 500,
            "status_code": resp.status_code,
        }
    except requests.exceptions.RequestException as e:
        return {
            "reachable": False,
            "status_code": None,
            "error": str(e),
        }