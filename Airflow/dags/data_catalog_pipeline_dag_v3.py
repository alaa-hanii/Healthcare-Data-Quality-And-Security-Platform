"""
DAG: data_catalog_pipeline
---------------------------------------------------------------------------
Linear pipeline calling the EXISTING FastAPI endpoints (main.py) over HTTP,
instead of importing ServicesLayer/*.py directly inside the Airflow worker.

WHY HTTP AND NOT DIRECT IMPORT:
  - DWH_service.py shells out to `dtexec` (SSIS) — Windows-only. Airflow
    runs inside a Linux Docker container, so dtexec is not available there.
  - quality_service / security_service / profiling_service rely on relative
    paths ("StorageLayer/...") and on pandas/pyspark/cryptography being
    installed in the SAME interpreter that runs them.
  - Your FastAPI app (main.py) already runs directly on the Windows host
    (confirmed), where dtexec + all the libraries + relative paths already
    work correctly. So Airflow just calls it over the network.

NETWORKING:
  Airflow containers -> Windows host FastAPI app:
      http://host.docker.internal:<PORT>
  This works out of the box with Docker Desktop for Windows.

ORCHESTRATION LOGGING:
  orchestration_endpoint.py's /log route is meant to be called by every
  layer when a run finishes (success or failure). Instead of adding a
  separate "log" task, this DAG calls it automatically via
  on_success_callback / on_failure_callback on every task.

⚠️ TODO — VERIFY AGAINST main.py:
  I don't have main.py, so the route prefixes below are my best guess
  from the router file names. Check how each router is mounted, e.g.:
      app.include_router(profiling_router, prefix="/profiling")
  and fix the *_PATH constants below if they don't match.

⚠️ INGESTION IS NOT IN THIS DAG:
  ingestion_service.run_ingestion(files) needs uploaded file objects —
  it's designed to run when a user uploads via the UI, not on a schedule.
  This DAG assumes ingestion already happened (files are in
  StorageLayer/LoadedData) before it starts at "profiling".
  Later, if you want full automation, ingestion_endpoint.py's /ingest
  handler could trigger this DAG run via Airflow's REST API right after
  a successful upload — ask me if you want that wired up.
"""

from datetime import datetime

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# Config — EDIT THESE to match your setup
# ---------------------------------------------------------------------------

BASE_URL = "http://host.docker.internal:8000"  # TODO: confirm your uvicorn port

PROFILING_PATH = "/profiling/profiling"          # POST  (profiling_endpoint.py)
QUALITY_PATH = "/quality/run-quality"             # GET   (quality_endpoint.py) needs ?token=
QUALITY_TOKEN = "admin123"                        # hardcoded fake_auth() in quality_endpoint.py
SECURITY_PATH = "/security/run"                   # POST  (security_endpoint.py)
DWH_PATH = "/dwh/run-all"                         # POST  (DWH_endpoint.py)
POWERBI_STATUS_PATH = "/powerbi/status"           # GET   (PowerBI_endpoint.py)
ORCH_LOG_PATH = "/orchestration/log"              # POST  (orchestration_endpoint.py)

REQUEST_TIMEOUT_SECONDS = {
    "profiling": 600,
    "quality": 1800,   # dq_engine.py can take a while
    "security": 600,
    "dwh": 1800,       # SSIS packages can be slow
    "powerbi": 60,
}


# ---------------------------------------------------------------------------
# Orchestration logging callbacks — fire automatically after every task
# ---------------------------------------------------------------------------

def _log_orchestration(context, status):
    ti = context["task_instance"]
    duration = ti.duration or 0
    exception = context.get("exception")
    message = str(exception) if exception else "ok"

    try:
        requests.post(
            f"{BASE_URL}{ORCH_LOG_PATH}",
            params={
                "layer": ti.task_id,
                "status": status,
                "message": message,
                "duration_seconds": duration,
            },
            timeout=10,
        )
    except Exception as log_err:
        # Never let logging failures break the pipeline
        print(f"[orchestration-log] could not log '{ti.task_id}': {log_err}")


def on_task_success(context):
    _log_orchestration(context, "success")


def on_task_failure(context):
    _log_orchestration(context, "failed")


# ---------------------------------------------------------------------------
# Task callables — each one just calls the existing endpoint
# ---------------------------------------------------------------------------

def call_profiling(**context):
    r = requests.post(f"{BASE_URL}{PROFILING_PATH}", timeout=REQUEST_TIMEOUT_SECONDS["profiling"])
    r.raise_for_status()
    print(r.json())


def call_quality(**context):
    r = requests.get(
        f"{BASE_URL}{QUALITY_PATH}",
        params={"token": QUALITY_TOKEN},
        timeout=REQUEST_TIMEOUT_SECONDS["quality"],
    )
    r.raise_for_status()
    print(r.json())


def call_security(**context):
    r = requests.post(f"{BASE_URL}{SECURITY_PATH}", timeout=REQUEST_TIMEOUT_SECONDS["security"])
    r.raise_for_status()
    data = r.json()
    print(data)
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"security layer error: {data['error']}")


def call_dwh(**context):
    r = requests.post(f"{BASE_URL}{DWH_PATH}", timeout=REQUEST_TIMEOUT_SECONDS["dwh"])
    r.raise_for_status()
    data = r.json()
    print(data)
    if data.get("status") != "success":
        raise RuntimeError(f"DWH pipeline failed: {data}")


def call_powerbi_status(**context):
    r = requests.get(f"{BASE_URL}{POWERBI_STATUS_PATH}", timeout=REQUEST_TIMEOUT_SECONDS["powerbi"])
    r.raise_for_status()
    print(r.json())


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

default_args = {
    "owner": "data-catalog-team",
    "retries": 1,
    "on_success_callback": on_task_success,
    "on_failure_callback": on_task_failure,
}

with DAG(
    dag_id="data_catalog_pipeline",
    description="Linear pipeline: profiling -> quality -> security -> DWH -> PowerBI check, via HTTP calls to main.py",
    default_args=default_args,
    schedule=None,  # trigger manually for now
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["data-catalog", "layers", "linear", "http"],
) as dag:

    # Task IDs are named to match the `dag_list` entries in UII.py's
    # orchestration_page() exactly (profiling_dag, data_quality_dag, ...).
    # Since on_task_success/on_task_failure log with layer=ti.task_id,
    # this makes the UI's DAGs table show REAL status from these runs
    # with zero extra wiring.
    t_profiling = PythonOperator(
        task_id="profiling_dag",
        python_callable=call_profiling,
    )

    t_quality = PythonOperator(
        task_id="data_quality_dag",
        python_callable=call_quality,
    )

    t_security = PythonOperator(
        task_id="security_dag",
        python_callable=call_security,
    )

    t_dwh = PythonOperator(
        task_id="stg_to_dwh_dag",
        python_callable=call_dwh,
    )

    t_powerbi = PythonOperator(
        task_id="powerbi_refresh_dag",
        python_callable=call_powerbi_status,
    )

    # Linear chain — stops automatically if any step fails
    t_profiling >> t_quality >> t_security >> t_dwh >> t_powerbi
