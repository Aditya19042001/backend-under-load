from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from prometheus_client import Counter, Histogram, Gauge
import time
import psutil
import os

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Active HTTP requests'
)

MEMORY_USAGE = Gauge(
    'app_memory_bytes',
    'Application memory usage'
)

CPU_USAGE = Gauge(
    'app_cpu_percent',
    'Application CPU usage'
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.inc()
        
        # Update system metrics
        process = psutil.Process(os.getpid())
        MEMORY_USAGE.set(process.memory_info().rss)
        CPU_USAGE.set(process.cpu_percent())
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            
            endpoint = request.url.path
            method = request.method
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            ACTIVE_REQUESTS.dec()
        
        return response