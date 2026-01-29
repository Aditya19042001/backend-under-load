from fastapi import APIRouter, Query
import time
import json
import hashlib

router = APIRouter()

def fibonacci(n: int) -> int:
    """Recursive fibonacci - intentionally inefficient"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def hash_computation(iterations: int) -> str:
    """CPU-intensive hashing"""
    result = "start"
    for i in range(iterations):
        result = hashlib.sha256(result.encode()).hexdigest()
    return result

@router.get("/cpu-intensive")
async def cpu_intensive(
    complexity: int = Query(default=30, ge=1, le=40, description="Fibonacci number to calculate")
):
    """CPU-bound operation - Fibonacci calculation"""
    start = time.time()
    result = fibonacci(complexity)
    duration = time.time() - start
    
    return {
        "result": result,
        "complexity": complexity,
        "duration_seconds": duration,
        "warning": "This endpoint is intentionally CPU-intensive"
    }

@router.get("/hash")
async def hash_endpoint(
    iterations: int = Query(default=10000, ge=1, le=100000)
):
    """CPU-intensive hashing operation"""
    start = time.time()
    result = hash_computation(iterations)
    duration = time.time() - start
    
    return {
        "hash": result,
        "iterations": iterations,
        "duration_seconds": duration
    }

@router.get("/json-processing")
async def json_processing(
    size: int = Query(default=1000, ge=1, le=10000)
):
    """CPU-intensive JSON serialization"""
    start = time.time()
    
    # Create large nested structure
    data = {
        f"key_{i}": {
            f"nested_{j}": f"value_{i}_{j}"
            for j in range(size)
        }
        for i in range(size)
    }
    
    # Serialize and deserialize multiple times
    for _ in range(5):
        serialized = json.dumps(data)
        data = json.loads(serialized)
    
    duration = time.time() - start
    
    return {
        "processed_items": size * size,
        "duration_seconds": duration,
        "data_size_bytes": len(serialized)
    }