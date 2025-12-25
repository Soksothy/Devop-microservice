"""
Observability components: logging, metrics, and tracing.
"""

import time
import logging
import uuid
from typing import Callable
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
import sys

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'inventory_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'inventory_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'inventory_active_requests',
    'Number of active requests'
)

DB_OPERATIONS = Counter(
    'inventory_db_operations_total',
    'Total number of database operations',
    ['operation', 'collection', 'status']
)

DB_OPERATION_DURATION = Histogram(
    'inventory_db_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'collection']
)

INVENTORY_ITEMS_TOTAL = Gauge(
    'inventory_items_total',
    'Total number of items in inventory'
)

INVENTORY_STOCK_VALUE = Gauge(
    'inventory_total_stock_quantity',
    'Total quantity of all items in stock'
)


class StructuredLogger:
    """Structured JSON logger for better log aggregation."""
    
    @staticmethod
    def setup_logger(name: str) -> logging.Logger:
        """Configure structured JSON logging."""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # JSON formatter
        json_handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(trace_id)s %(method)s %(path)s'
        )
        json_handler.setFormatter(formatter)
        logger.addHandler(json_handler)
        
        return logger


class RequestTracingMiddleware:
    """Middleware for request tracing with correlation IDs."""
    
    def __init__(self, app):
        self.app = app
        self.logger = StructuredLogger.setup_logger("request_tracer")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        scope["trace_id"] = trace_id
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add trace ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            ACTIVE_REQUESTS.dec()
            
            # Log request
            self.logger.info(
                "Request completed",
                extra={
                    "trace_id": trace_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "duration": duration
                }
            )


async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to track request metrics."""
    method = request.method
    endpoint = request.url.path
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Record metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
        
        return response
    
    except Exception as e:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
        raise e


async def get_prometheus_metrics():
    """Endpoint to expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


class DatabaseMetrics:
    """Helper class to track database operation metrics."""
    
    @staticmethod
    def track_operation(operation: str, collection: str):
        """Context manager to track database operations."""
        class OperationTracker:
            def __init__(self, op: str, coll: str):
                self.operation = op
                self.collection = coll
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                status = "error" if exc_type else "success"
                
                DB_OPERATIONS.labels(
                    operation=self.operation,
                    collection=self.collection,
                    status=status
                ).inc()
                
                DB_OPERATION_DURATION.labels(
                    operation=self.operation,
                    collection=self.collection
                ).observe(duration)
                
                return False  # Don't suppress exceptions
        
        return OperationTracker(operation, collection)
