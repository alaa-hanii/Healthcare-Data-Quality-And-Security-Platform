import pandas as pd
import os
import zipfile
from ydata_profiling import ProfileReport

DATA_PATH = "StorageLayer/LoadedData/"
REPORT_PATH = "StorageLayer/reports/"

def generate_reports():
    os.makedirs(REPORT_PATH, exist_ok=True)

    report_files = []

    for file in os.listdir(DATA_PATH):
        if file.endswith(".csv"):

            file_path = os.path.join(DATA_PATH, file)
            df = pd.read_csv(file_path)

            name = file.replace(".csv", "")

            report = ProfileReport(
                df,
                title=f"Profiling Report - {name}",
                explorative=True
            )

            output_file = os.path.join(REPORT_PATH, f"{name}.html")
            report.to_file(output_file)

            report_files.append(output_file)

    # ZIP
    zip_path = os.path.join(REPORT_PATH, "All_Reports.zip")

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for f in report_files:
            zipf.write(f, os.path.basename(f))

    return zip_path