from fastapi import APIRouter, HTTPException, Query
import httpx
import asyncio
from app.core.config import settings
import time

router = APIRouter()

@router.get("/call-downstream")
async def call_downstream(
    timeout: int = Query(default=5, ge=1, le=60)
):
    """Calls downstream service with configurable timeout"""
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{settings.DOWNSTREAM_SERVICE_URL}/slow",
                params={"delay": 3}
            )
            duration = time.time() - start
            
            return {
                "status": "success",
                "downstream_response": response.json(),
                "duration_seconds": duration,
                "timeout_configured": timeout
            }
    except httpx.TimeoutException:
        duration = time.time() - start
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Downstream service timeout",
                "duration_seconds": duration,
                "timeout_configured": timeout
            }
        )
    except Exception as e:
        duration = time.time() - start
        raise HTTPException(
            status_code=502,
            detail={
                "error": f"Downstream service error: {str(e)}",
                "duration_seconds": duration
            }
        )

@router.get("/cascade-failure")
async def cascade_failure():
    """Simulates cascade failure with multiple downstream calls"""
    start = time.time()
    
    async def call_service(service_num: int):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{settings.DOWNSTREAM_SERVICE_URL}/slow",
                    params={"delay": 2}
                )
                return {"service": service_num, "status": "success", "data": response.json()}
        except Exception as e:
            return {"service": service_num, "status": "failed", "error": str(e)}
    
    # Call 5 downstream services in parallel
    tasks = [call_service(i) for i in range(5)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start
    
    return {
        "total_calls": 5,
        "duration_seconds": duration,
        "results": results
    }

@router.get("/no-timeout")
async def no_timeout_configured():
    """Dangerous: No timeout configured"""
    try:
        async with httpx.AsyncClient() as client:  # No timeout!
            response = await client.get(
                f"{settings.DOWNSTREAM_SERVICE_URL}/slow",
                params={"delay": 30}
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))