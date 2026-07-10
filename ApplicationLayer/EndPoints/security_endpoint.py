from fastapi import APIRouter, Query
from ServicesLayer.security_service import run_security, decrypt_data

router = APIRouter()

@router.post("/run")
def run_security_layer():
    return run_security()

@router.get("/decrypt")
def decrypt(username: str = Query(...)):
    return decrypt_data(username)