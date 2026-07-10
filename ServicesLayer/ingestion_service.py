# =========================
# Ingestion Service
# =========================

from ProcessingLayer.ingestion.spark_loader import save_files, load_data, inspect_data

async def run_ingestion(files):

    # 1. Save files
    saved_paths = save_files(files)

    # 2. Load with Spark
    tables = load_data(saved_paths)

    # 3. Inspect
    metadata = inspect_data(tables)

    return {
        "status": "success",
        "tables_loaded": list(tables.keys()),
        "details": metadata
    }