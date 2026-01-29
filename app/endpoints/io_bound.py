from fastapi import APIRouter, Query
import asyncio
import time
import random

router = APIRouter()

@router.get("/slow")
async def slow_endpoint(
    delay: int = Query(default=5, ge=1, le=30, description="Delay in seconds")
):
    """Simulates slow I/O operation"""
    start = time.time()
    await asyncio.sleep(delay)
    duration = time.time() - start
    
    return {
        "status": "completed",
        "requested_delay": delay,
        "actual_duration": duration,
        "message": f"Slept for {delay} seconds"
    }

@router.get("/random-delay")
async def random_delay():
    """Random delay to simulate unpredictable I/O"""
    delay = random.uniform(0.5, 5.0)
    await asyncio.sleep(delay)
    
    return {
        "status": "completed",
        "delay_seconds": delay
    }

@router.get("/blocking")
def blocking_endpoint(
    duration: int = Query(default=5, ge=1, le=30)
):
    """Intentionally blocking endpoint (sync sleep)"""
    time.sleep(duration)
    return {
        "status": "completed",
        "blocked_for": duration,
        "warning": "This endpoint blocks the worker thread"
    }

@router.get("/parallel-io")
async def parallel_io(
    count: int = Query(default=5, ge=1, le=20)
):
    """Simulates multiple parallel I/O operations"""
    start = time.time()
    
    async def fake_io_task(task_id: int):
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
        return {"task_id": task_id, "delay": delay}
    
    tasks = [fake_io_task(i) for i in range(count)]
    results = await asyncio.gather(*tasks)
    
    duration = time.time() - start
    
    return {
        "total_tasks": count,
        "total_duration": duration,
        "results": results
    }