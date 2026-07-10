import os
import pandas as pd

DATA_PATH = "StorageLayer/LoadedData/"
OUTPUT_PATH = "StorageLayer/reports/"


def run_profiling():
    try:
        os.makedirs(OUTPUT_PATH, exist_ok=True)

        reports = []

        for file in os.listdir(DATA_PATH):
            if file.endswith(".csv"):
                path = os.path.join(DATA_PATH, file)

                df = pd.read_csv(path)

                report = {
                    "file": file,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "nulls": df.isnull().sum().to_dict()
                }

                reports.append(report)

        return reports

    except Exception as e:
        return {"error": str(e)}





from ProcessingLayer.profiling import generate_reports

def run_profiling():
    zip_path = generate_reports()

    return {
        "status": "success",
        "files": {
            "zip": zip_path
        }
    }
