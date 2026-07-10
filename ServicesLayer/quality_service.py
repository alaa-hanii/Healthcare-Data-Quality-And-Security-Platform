import subprocess
import os
import sys
import pandas as pd

DQ_ENGINE = "ProcessingLayer/dq_engine.py"
REPORT_PATH = "StorageLayer/DataQualityReports"


def run_dq():
    try:
        python_exec = sys.executable
        result = subprocess.run(
            [python_exec, DQ_ENGINE],
            check=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        return {"status": "DQ Completed", "log": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}


def get_report():
    try:
        all_rows = []

        for entry in os.listdir(REPORT_PATH):
            entry_path = os.path.join(REPORT_PATH, entry)

            if entry.endswith(".csv") and os.path.isfile(entry_path):
                all_rows.append(pd.read_csv(entry_path))

            elif os.path.isdir(entry_path):
                for fname in os.listdir(entry_path):
                    if fname.startswith("part-") and fname.endswith(".csv"):
                        all_rows.append(pd.read_csv(os.path.join(entry_path, fname)))

        if not all_rows:
            return {"error": "No reports found"}

        combined = pd.concat(all_rows, ignore_index=True)
        return combined.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}