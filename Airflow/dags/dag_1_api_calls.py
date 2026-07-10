"""
DAG 1: dag_api_calls.py
════════════════════════════════════════════════════════
الأسلوب: HTTP calls للـ FastAPI endpoints مباشرة
الفلسفة: Airflow = "متى؟" | FastAPI = "الشغل نفسه"
════════════════════════════════════════════════════════
"""

from datetime import datetime, timedelta
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

# ── Config ──────────────────────────────────────────
BASE_URL      = "http://host.docker.internal:8000"
QUALITY_TOKEN = "admin123"

default_args = {
    "owner"          : "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry" : False,
    "retries"        : 1,
    "retry_delay"    : timedelta(minutes=5),
}

# ── Task Functions ───────────────────────────────────

def call_profiling():
    r = requests.post(f"{BASE_URL}/profiling/profiling", timeout=600)
    r.raise_for_status()
    result = r.json()
    print("[profiling]", result)

def call_quality():
    r = requests.get(f"{BASE_URL}/quality/run-quality",
                     params={"token": QUALITY_TOKEN}, timeout=1800)
    r.raise_for_status()
    result = r.json()
    print("[quality]", result)

def call_security():
    r = requests.post(f"{BASE_URL}/security/run", timeout=600)
    r.raise_for_status()
    result = r.json()
    print("[security]", result)

def call_dwh():
    r = requests.post(f"{BASE_URL}/dwh/run-all", timeout=1800)
    r.raise_for_status()
    result = r.json()
    print("[dwh]", result)
    if result.get("status") != "success":
        raise RuntimeError(f"DWH failed: {result}")

def call_powerbi():
    r = requests.get(f"{BASE_URL}/powerbi/status", timeout=60)
    r.raise_for_status()
    print("[powerbi]", r.json())

# ── DAG ─────────────────────────────────────────────

with DAG(
    dag_id      = "dag_1_api_calls",
    description = "Pipeline via HTTP calls to FastAPI endpoints",
    default_args= default_args,
    schedule    = "@hourly",
    start_date  = datetime(2026, 1, 1, 8, 0),
    catchup     = False,
    max_active_runs = 1,
    tags        = ["method-api", "http"],
) as dag:

    t1 = PythonOperator(task_id="profiling", python_callable=call_profiling)
    t2 = PythonOperator(task_id="quality",   python_callable=call_quality)
    t3 = PythonOperator(task_id="security",  python_callable=call_security)
    t4 = PythonOperator(task_id="dwh",       python_callable=call_dwh)
    t5 = PythonOperator(task_id="powerbi",   python_callable=call_powerbi)

    t1 >> t2 >> t3 >> t4 >> t5
