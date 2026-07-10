from fastapi import APIRouter
from ServicesLayer.profiling_service import run_profiling

router = APIRouter()

@router.post("/profiling")
def run_profiling_api():
    result = run_profiling()
    return {
        "status": "success",
        "files": result
    }