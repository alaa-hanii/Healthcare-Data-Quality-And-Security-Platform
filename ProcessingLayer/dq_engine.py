import os
import sys
import uuid
from datetime import datetime

# =========================
# Environment Fix (Windows + PySpark)
# =========================
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# =========================
# Spark Session
# =========================
spark = SparkSession.builder \
    .appName("DQ Engine") \
    .config("spark.ui.enabled", "false") \
    .config("spark.sql.autoBroadcastJoinThreshold", "-1") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("DQ Engine Started...")

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_PATH  = os.path.join(BASE_DIR, "..", "StorageLayer", "LoadedData")
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "StorageLayer", "DataQualityReports")

os.makedirs(OUTPUT_PATH, exist_ok=True)

print("INPUT_PATH:", INPUT_PATH)
print("OUTPUT_PATH:", OUTPUT_PATH)

# =========================
# Load Tables
# =========================
tables = {}

if not os.path.exists(INPUT_PATH):
    raise Exception(f"Input path not found: {INPUT_PATH}")

for file in os.listdir(INPUT_PATH):
    if file.endswith(".csv"):
        table_name = file.replace(".csv", "")
        file_path  = os.path.join(INPUT_PATH, file)
        print(f"Loading: {file_path}")
        df = spark.read.option("header", True).option("inferSchema", True).csv(file_path)
        tables[table_name] = df

print("Tables Loaded:", list(tables.keys()))

# =========================
# DQ Rules
# =========================
dq_rules = {
    "patients":        {"pk": "patient_id",      "fk": {"department_id": "departments"}},
    "doctors":         {"pk": "doctor_id",        "fk": {"department_id": "departments"}},
    "appointments":    {"pk": "appointment_id",   "fk": {"patient_id": "patients", "doctor_id": "doctors"}},
    "admissions":      {"pk": "admission_id",     "fk": {"patient_id": "patients", "room_id": "rooms", "bed_id": "beds"}},
    "nurses":          {"pk": "nurse_id",         "fk": {"department_id": "departments"}},
    "equipment":       {"pk": "equipment_id",     "fk": {"department_id": "departments"}},
    "medical_history": {"pk": "history_id",       "fk": {"patient_id": "patients", "appointment_id": "appointments"}},
    "notifications":   {"pk": "notification_id",  "fk": {"appointment_id": "appointments"}},
    "beds":            {"pk": "bed_id",           "fk": {"room_id": "rooms"}},
    "rooms":           {"pk": "room_id",          "fk": {"department_id": "departments"}},
    "departments":     {"pk": "department_id",    "fk": {}},
}

# =========================
# Thresholds
# =========================
dq_thresholds = {
    "completeness":  0.90,
    "uniqueness":    0.00,
    "fk_error_rate": 0.05,
}


def calc_rate(error, total):
    return 0 if total == 0 else error / total


# =========================
# DQ Check Functions
# =========================
def completeness_gate(df, table):
    total_cells = len(df.columns) * df.count()
    nulls = sum(df.filter(col(c).isNull()).count() for c in df.columns)
    rate = calc_rate(nulls, total_cells)
    status = "FAIL" if rate > (1 - dq_thresholds["completeness"]) else "PASS"
    return (table, "completeness", int(nulls), int(total_cells), round(rate, 4), status)


def uniqueness_gate(df, pk, table):
    if pk not in df.columns:
        return (table, "uniqueness", 0, 0, 0.0, "SKIPPED")
    total = df.count()
    duplicates = df.groupBy(pk).count().filter("count > 1").count()
    rate = calc_rate(duplicates, total)
    status = "FAIL" if rate > dq_thresholds["uniqueness"] else "PASS"
    return (table, "uniqueness", int(duplicates), int(total), round(rate, 4), status)


def fk_gate(df, col_name, ref_df, ref_pk, table):
    if col_name not in df.columns or ref_pk not in ref_df.columns:
        return (table, f"fk_{col_name}", 0, 0, 0.0, "SKIPPED")
    try:
        from pyspark.sql.functions import col as sc, trim
        from pyspark.sql.types import StringType

        # Cast both sides to string to avoid BIGINT cast errors on text IDs
        df_cast     = df.withColumn("_fk_left",  sc(col_name).cast(StringType()))
        ref_cast    = ref_df.withColumn("_fk_right", sc(ref_pk).cast(StringType()))

        total   = df_cast.count()
        invalid = df_cast.join(
            ref_cast,
            df_cast["_fk_left"] == ref_cast["_fk_right"],
            "left_anti"
        ).count()

        rate   = calc_rate(invalid, total)
        status = "FAIL" if rate > dq_thresholds["fk_error_rate"] else "PASS"
        return (table, f"fk_{col_name}", int(invalid), int(total), round(rate, 4), status)
    except Exception as e:
        print(f"WARNING: FK check skipped for {table}.{col_name} → {e}")
        return (table, f"fk_{col_name}", 0, 0, 0.0, "SKIPPED")


# =========================
# Engine Core
# =========================
def run_dq_gate(tables, rules):
    report = []
    for table_name, df in tables.items():
        r   = rules.get(table_name, {})
        pk  = r.get("pk")
        fks = r.get("fk", {})

        report.append(completeness_gate(df, table_name))

        if pk:
            report.append(uniqueness_gate(df, pk, table_name))

        for fk_col, ref_table in fks.items():
            if ref_table in tables:
                report.append(fk_gate(
                    df, fk_col,
                    tables[ref_table],
                    rules[ref_table]["pk"],
                    table_name
                ))
    return report


# =========================
# Run
# =========================
print("Running Data Quality Checks...")

gate_report = run_dq_gate(tables, dq_rules)

# Build as pandas DataFrame directly — avoids NativeIO$Windows Spark write bug on Windows
import pandas as pd

gate_pd = pd.DataFrame(gate_report,
    columns=["Table", "Metric", "Error_Count", "Total", "Error_Rate", "Status"])

run_id    = str(uuid.uuid4())
timestamp = str(datetime.now())

gate_pd["run_id"]    = run_id
gate_pd["timestamp"] = timestamp

# Save as a single CSV file (pandas, not Spark) — no Hadoop NativeIO needed
output_file = os.path.join(OUTPUT_PATH, f"dq_report_{run_id}.csv")
gate_pd.to_csv(output_file, index=False)

print(f"DQ Report Saved: {output_file}")
print("Done!")

