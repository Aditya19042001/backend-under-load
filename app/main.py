from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging
from contextlib import asynccontextmanager

from app.endpoints import healthy, cpu_bound, io_bound, downstream, memory_ops, database
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.core.database import init_db, close_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    await init_db()
    yield
    logger.info("Shutting down application...")
    await close_db()

app = FastAPI(
    title="Load Testing Backend",
    description="Backend for demonstrating system behavior under load",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

app.include_router(healthy.router, prefix="/api", tags=["health"])
app.include_router(cpu_bound.router, prefix="/api", tags=["cpu"])
app.include_router(io_bound.router, prefix="/api", tags=["io"])
app.include_router(downstream.router, prefix="/api", tags=["downstream"])
app.include_router(memory_ops.router, prefix="/api", tags=["memory"])
app.include_router(database.router, prefix="/api", tags=["database"])

@app.get("/")
async def root():
    return {"service": "load-testing-backend", "version": "1.0.0", "status": "healthy"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}