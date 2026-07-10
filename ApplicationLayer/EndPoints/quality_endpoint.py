from fastapi import APIRouter, HTTPException
import subprocess
import pandas as pd
import os
import sys

from ServicesLayer.quality_service import run_dq

router = APIRouter()

REPORT_PATH = "StorageLayer/DataQualityReports"

# =========================
# Auth
# =========================
def fake_auth(token: str = ""):
    if token != "admin123":
        raise HTTPException(status_code=401, detail="Unauthorized")


# =========================
# Root
# =========================
@router.get("/")
def quality():
    return {"message": "Quality Layer Ready"}


# =========================
# Run Quality Engine
# =========================
@router.get("/run-quality")
def run_quality(token: str = ""):
    fake_auth(token)

    try:
        # Use same python interpreter as the running server (Anaconda)
        python_exec = sys.executable

        result = subprocess.run(
            [python_exec, "ProcessingLayer/dq_engine.py"],
            check=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        print("DQ STDOUT:", result.stdout)
        print("DQ STDERR:", result.stderr)
        return {"message": "DQ Process Completed Successfully", "log": result.stdout}

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DQ Engine failed: {e.stderr}"
        )


# =========================
# Get Latest Report
# =========================
@router.get("/get-quality-report")
def get_quality_report(token: str = ""):
    fake_auth(token)

    try:
        if not os.path.exists(REPORT_PATH):
            return {"error": f"Report folder does not exist: {REPORT_PATH}"}

        # DQ engine saves as subfolder (Spark partitioned output)
        # Each subfolder contains part-*.csv files
        all_rows = []

        entries = os.listdir(REPORT_PATH)

        for entry in entries:
            entry_path = os.path.join(REPORT_PATH, entry)

            # Case 1: direct CSV file
            if entry.endswith(".csv") and os.path.isfile(entry_path):
                df = pd.read_csv(entry_path)
                all_rows.append(df)

            # Case 2: Spark partitioned subfolder (dq_report_<uuid>/)
            elif os.path.isdir(entry_path):
                for fname in os.listdir(entry_path):
                    if fname.startswith("part-") and fname.endswith(".csv"):
                        fpath = os.path.join(entry_path, fname)
                        df = pd.read_csv(fpath)
                        all_rows.append(df)

        if not all_rows:
            return {"error": "No report CSV files found yet"}

        # Combine all parts
        combined = pd.concat(all_rows, ignore_index=True)

        if combined.empty:
            return {"error": "Report is empty"}

        return combined.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}