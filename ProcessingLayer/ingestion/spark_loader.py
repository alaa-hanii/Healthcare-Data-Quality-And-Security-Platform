# store uploaded files in the StorageLayer/LoadedData directory

import os
from fastapi import UploadFile
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("IngestionLayer") \
    .config("spark.driver.host", "127.0.0.1") \
    .getOrCreate()

spark = SparkSession.builder.appName("IngestionLayer").getOrCreate()

DATA_PATH = "StorageLayer/LoadedData/"

def save_files(files):
    os.makedirs(DATA_PATH, exist_ok=True)

    saved_paths = []

    for file in files:
        file_path = os.path.join(DATA_PATH, file.filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        saved_paths.append(file_path)

    return saved_paths


# Load data with Spark and return a dictionary of DataFrames keyed by table name

def load_data(paths):
    tables = {}

    for path in paths:
        name = os.path.basename(path).replace(".csv", "")

        df = spark.read \
            .option("header", True) \
            .option("inferSchema", True) \
            .option("multiLine", True) \
            .option("quote", '"') \
            .option("escape", '"') \
            .csv(path)

        tables[name] = df

    return tables


# Inspect data and return metadata

def inspect_data(tables):
    result = {}

    for name, df in tables.items():

        total_rows = df.count()

        # Missing values
        missing = {
            col: df.filter(df[col].isNull()).count()
            for col in df.columns
        }

        # Stats (for numeric columns only)
        numeric_cols = [c for c, t in df.dtypes if t in ["int", "double", "float"]]

        stats = {}
        if numeric_cols:
            desc = df.select(numeric_cols).describe().toPandas().to_dict()

            for col in numeric_cols:
                stats[col] = {
                    "mean": desc[col].get("mean"),
                    "min": desc[col].get("min"),
                    "max": desc[col].get("max")
                }

        result[name] = {
            "rows": total_rows,
            "columns": df.columns,
            "missing_values": missing,
            "stats": stats,
            "sample": [row.asDict() for row in df.limit(5).collect()]
        }

    return result