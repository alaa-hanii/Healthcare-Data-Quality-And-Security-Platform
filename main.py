from fastapi import FastAPI

# ========================= 
# Import Routers
# =========================
from ApplicationLayer.EndPoints.ingestion_endpoint import router as ingestion_router
from ApplicationLayer.EndPoints.profiling_endpoint  import router as profiling_router
from ApplicationLayer.EndPoints.quality_endpoint    import router as quality_router
from ApplicationLayer.EndPoints.security_endpoint   import router as security_router
from ApplicationLayer.EndPoints.DWH_endpoint        import router as dwh_router   # ← NEW
from ApplicationLayer.EndPoints.PowerBI_endpoint     import router as powerbi_router   # ← NEW
from ApplicationLayer.EndPoints.orchestration_endpoint import router as orchestration_router   # ← NEW

app = FastAPI(
    title="Data Platform API",
    description="Ingestion | Profiling | Data Quality | Security | DWH | Power BI | Orchestration",
    version="1.0"
)

# =========================
# Register Routers
# =========================
app.include_router(ingestion_router, prefix="/ingestion", tags=["Ingestion"])
app.include_router(profiling_router, prefix="/profiling", tags=["Profiling"])
app.include_router(quality_router,   prefix="/quality",   tags=["Data Quality"])
app.include_router(security_router,  prefix="/security",  tags=["Security"])
app.include_router(dwh_router,       prefix="/dwh",       tags=["DWH"])           # ← NEW
app.include_router(powerbi_router,   prefix="/powerbi",   tags=["Power BI"])      # ← NEW
app.include_router(orchestration_router, prefix="/orchestration", tags=["Orchestration"])   # ← NEW

# =========================
# Health Check
# =========================
@app.get("/")
def home():
    return {"message": "Data Quality Platform is Running "}