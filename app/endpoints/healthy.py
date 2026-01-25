from fastapi import APIRouter, Response
import time

router = APIRouter()

@router.get("/fast")
async def fast_endpoint():
    """Fast endpoint - returns immediately"""
    return {
        "status": "success",
        "message": "This is a fast endpoint",
        "timestamp": time.time()
    }

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}