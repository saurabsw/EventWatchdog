from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.tsdb_client import tsdb_client
from app.core.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(db: Session = Depends(get_db)):
    """Health and readiness check for application and underlying stores."""
    # Check SQLite
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check VictoriaMetrics
    vm_ok = await tsdb_client.check_health()

    overall_status = "healthy" if db_ok else "degraded"
    if not vm_ok:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        services={
            "sqlite": "healthy" if db_ok else "unhealthy",
            "victoriametrics": "healthy" if vm_ok else "unavailable (offline/standalone)"
        }
    )
