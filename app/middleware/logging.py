from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import logging
import uuid

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s",
            extra={"request_id": request_id, "duration": duration}
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(duration)
        
        return response