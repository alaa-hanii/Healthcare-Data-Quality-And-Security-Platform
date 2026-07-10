
import subprocess, time
# المسارات اللي شغالة فعليًا (نجحت بـ DTSER_SUCCESS من الـ CMD)
STG_PATH = r"C:\Projects\Project3\DataCatalogArchitecture\ProcessingLayer\DWH\DWH\Load_To_Staging\Hospital_stag\Hospital_stag\Package.dtsx"
DWH_PATH = r"C:\Projects\Project3\DataCatalogArchitecture\ProcessingLayer\DWH\DWH\Load_To_DWH\Data_Ware_House\Data_Ware_House\Package.dtsx"

DTEXEC = r"C:\Program Files\Microsoft SQL Server\170\DTS\Binn\DTExec.exe"

def execute_package(path: str) -> dict:
    start = time.time()
    result = subprocess.run([DTEXEC, "/FILE", path], capture_output=True, text=True)
    return {
        "status": "success" if result.returncode == 0 else "failed",
        "elapsed": round(time.time() - start, 2),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def run_stg():
    return execute_package(STG_PACKAGE)

def run_dwh():
    return execute_package(DWH_PACKAGE)

def run_pipeline():
    stg = execute_package(STG_PACKAGE)
    dwh = execute_package(DWH_PACKAGE)
    return {"stg": stg, "dwh": dwh, "status": "success" if stg["status"] == dwh["status"] == "success" else "failed"}