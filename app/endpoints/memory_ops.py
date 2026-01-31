from fastapi import APIRouter, Query
import time

router = APIRouter()

# Global list to simulate memory leak
memory_hog = []

@router.get("/memory-leak")
async def memory_leak(
    size_mb: int = Query(default=10, ge=1, le=100)
):
    """Intentional memory leak - allocates memory and never frees it"""
    # Allocate approximately size_mb megabytes
    chunk_size = 1024 * 1024  # 1 MB
    data = bytearray(chunk_size * size_mb)
    memory_hog.append(data)
    
    return {
        "allocated_mb": size_mb,
        "total_allocations": len(memory_hog),
        "warning": "Memory will not be freed until pod restart"
    }

@router.get("/memory-spike")
async def memory_spike(
    size_mb: int = Query(default=50, ge=1, le=500)
):
    """Temporary memory spike - allocates and frees"""
    start = time.time()
    
    # Allocate large chunk
    chunk_size = 1024 * 1024
    data = bytearray(chunk_size * size_mb)
    
    # Simulate some work
    import time as t
    t.sleep(1)
    
    # Data will be garbage collected after function returns
    duration = time.time() - start
    
    return {
        "allocated_mb": size_mb,
        "duration_seconds": duration,
        "note": "Memory will be freed by garbage collector"
    }

@router.post("/clear-memory")
async def clear_memory():
    """Clear the memory leak (for testing)"""
    global memory_hog
    count = len(memory_hog)
    memory_hog.clear()
    
    return {
        "cleared_allocations": count,
        "status": "memory cleared"
    }