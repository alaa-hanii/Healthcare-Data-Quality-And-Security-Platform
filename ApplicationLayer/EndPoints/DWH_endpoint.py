from fastapi import APIRouter
import subprocess, time, os, shutil

router = APIRouter()

# المسارات اللي شغالة فعليًا (نجحت بـ DTSER_SUCCESS من الـ CMD)
STG_PATH = r"C:\Projects\Project3\DataCatalogArchitecture\ProcessingLayer\DWH\DWH\Load_To_Staging\Hospital_stag\Hospital_stag\Package.dtsx"
DWH_PATH = r"C:\Projects\Project3\DataCatalogArchitecture\ProcessingLayer\DWH\DWH\Load_To_DWH\Data_Ware_House\Data_Ware_House\Package.dtsx"

DTEXEC = r"C:\Program Files\Microsoft SQL Server\170\DTS\Binn\DTExec.exe"

def _run(path: str) -> dict:
    start = time.time()
    try:
        result = subprocess.run(
            [DTEXEC, "/FILE", path],
            capture_output=True, text=True, timeout=1200
        )
        ok = result.returncode == 0
        return {
            "status":          "success" if ok else "failed",
            "message":         "Package completed successfully." if ok else "Package failed — see stdout/stderr.",
            "elapsed_seconds": round(time.time() - start, 2),
            "returncode":      result.returncode,
            "stdout":          result.stdout[-3000:],
            "stderr":          result.stderr[-1500:],
        }
    except subprocess.TimeoutExpired:
        return {"status": "failed", "message": "Timed out after 20 minutes.", "elapsed_seconds": 1200}
    except FileNotFoundError:
        return {"status": "failed", "message": "dtexec not found on PATH."}


@router.get("/status")
def status():
    return {
        "dtexec_found": shutil.which("dtexec") is not None,
        "dtexec_path":  shutil.which("dtexec"),
        "packages": {
            "Load-to-STG.dtsx": {"exists": os.path.exists(STG_PATH), "path": STG_PATH},
            "Load-to-DWH.dtsx": {"exists": os.path.exists(DWH_PATH), "path": DWH_PATH},
        }
    }


@router.post("/run-stg")
def run_stg():
    return _run(STG_PATH)


@router.post("/run-dwh")
def run_dwh():
    return _run(DWH_PATH)


@router.post("/run-all")
def run_all():
    stg = _run(STG_PATH)
    if stg["status"] != "success":
        return {"status": "failed", "stg": stg, "dwh": None}
    dwh = _run(DWH_PATH)
    return {
        "status": "success" if dwh["status"] == "success" else "failed",
        "stg": stg,
        "dwh": dwh,
    }