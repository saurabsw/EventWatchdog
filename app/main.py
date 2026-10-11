import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, setup_logging
from app.core.database import init_db
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.logs import router as logs_router
from app.api.monitors import router as monitors_router
from app.api.incidents import router as incidents_router
from app.api.models import router as models_router
from app.api.metadata import router as metadata_router
from app.ui.router import router as ui_router
from app.workers.evaluator import evaluator_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    init_db()
    # Run background evaluator task
    eval_task = asyncio.create_task(evaluator_worker.start())
    yield
    # Shutdown
    evaluator_worker.stop()
    eval_task.cancel()


app = FastAPI(
    title="Intelligent Observability & Event Watchdog",
    description="API-first Observability, Metric Ingestion, Static Alerting and Statistical Anomaly Detection",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routes
app.include_router(health_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")
app.include_router(monitors_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(metadata_router, prefix="/api/v1")

# UI router
app.include_router(ui_router, prefix="/ui")


@app.get("/")
async def root():
    return {
        "name": "Intelligent Observability & Event Watchdog",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "ui": "/ui"
    }
