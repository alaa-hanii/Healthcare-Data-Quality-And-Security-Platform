# =========================
# Ingestion Endpoint
# =========================
# Purpose:
# - Receive files from UI
# - Send them to service
# - Return metadata

from fastapi import APIRouter, UploadFile, File
from typing import List
from ServicesLayer.ingestion_service import run_ingestion

router = APIRouter()

@router.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    result = await run_ingestion(files)
    return result