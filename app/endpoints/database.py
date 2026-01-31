from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.task import Task
import asyncio
import time

router = APIRouter()

@router.post("/tasks")
async def create_task(
    title: str,
    description: str = "",
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    task = Task(title=title, description=description)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return {"task_id": task.id, "title": task.title}

@router.get("/tasks")
async def list_tasks(
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List tasks with pagination"""
    result = await db.execute(select(Task).limit(limit))
    tasks = result.scalars().all()
    
    return {
        "count": len(tasks),
        "tasks": [{"id": t.id, "title": t.title} for t in tasks]
    }

@router.get("/db-pool-exhaust")
async def exhaust_db_pool(
    concurrent_queries: int = Query(default=10, ge=1, le=50)
):
    """
    Attempts to exhaust the database connection pool
    If concurrent_queries > pool_size, some will timeout
    """
    start = time.time()
    
    async def slow_query(query_id: int, db: AsyncSession):
        try:
            # Hold connection for 5 seconds
            await db.execute(select(func.pg_sleep(5)))
            return {"query_id": query_id, "status": "success"}
        except Exception as e:
            return {"query_id": query_id, "status": "failed", "error": str(e)}
    
    # This will fail if not using dependency injection properly
    # Demonstrating pool exhaustion
    tasks = []
    for i in range(concurrent_queries):
        # Note: In real scenario, each request would get its own session
        # This is simplified for demonstration
        task = asyncio.create_task(
            slow_query(i, await anext(get_db()))
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start
    
    return {
        "concurrent_queries": concurrent_queries,
        "duration_seconds": duration,
        "results": results,
        "warning": "Some queries may have timed out if pool size exceeded"
    }

@router.get("/expensive-query")
async def expensive_query(
    iterations: int = Query(default=1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Simulates an expensive database query"""
    start = time.time()
    
    # Create many tasks
    for i in range(iterations):
        task = Task(title=f"Task {i}", description=f"Generated task {i}")
        db.add(task)
    
    await db.commit()
    
    # Expensive query with aggregation
    result = await db.execute(
        select(func.count(Task.id))
    )
    count = result.scalar()
    
    duration = time.time() - start
    
    return {
        "created_tasks": iterations,
        "total_tasks": count,
        "duration_seconds": duration
    }