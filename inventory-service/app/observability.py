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

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor


def setup_tracing(service_name: str = "inventory-service", jaeger_host: str = "localhost", jaeger_port: int = 6831):
    """
    Configure OpenTelemetry tracing with Jaeger exporter.
    
    Args:
        service_name: Name of the service for tracing
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port (default: 6831 for UDP)
    """
    # Create a resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    # Add span processor
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Auto-instrument FastAPI
    FastAPIInstrumentor().instrument()
    
    # Auto-instrument PyMongo
    PymongoInstrumentor().instrument()
    
    return trace.get_tracer(__name__)


# Get tracer for manual instrumentation
tracer = trace.get_tracer(__name__)

# Prometheus Metrics - HTTP
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUESTS_INPROGRESS = Gauge(
    'http_requests_inprogress',
    'HTTP requests currently being processed',
    ['method', 'endpoint']
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

HTTP_REQUEST_SIZE_BYTES = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# Prometheus Metrics - Application Specific
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
    """Middleware for request tracing with correlation IDs and HTTP metrics."""
    
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
        
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Track active requests
        ACTIVE_REQUESTS.inc()
        HTTP_REQUESTS_INPROGRESS.labels(method=method, endpoint=path).inc()
        
        start_time = time.time()
        status_code = 500  # Default to error
        request_size = 0
        response_size = 0
        
        # Calculate request size
        if "headers" in scope:
            for header, value in scope["headers"]:
                request_size += len(header) + len(value)
        
        async def send_wrapper(message):
            nonlocal status_code, response_size
            
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                
                # Add trace ID to response headers
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
                
                # Calculate response header size
                for header, value in headers:
                    response_size += len(header) + len(value)
            
            elif message["type"] == "http.response.body":
                # Add response body size
                body = message.get("body", b"")
                response_size += len(body)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            
            # Decrement active request counters
            ACTIVE_REQUESTS.dec()
            HTTP_REQUESTS_INPROGRESS.labels(method=method, endpoint=path).dec()
            
            # Record HTTP metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).observe(duration)
            
            HTTP_REQUEST_SIZE_BYTES.labels(
                method=method,
                endpoint=path
            ).observe(request_size)
            
            HTTP_RESPONSE_SIZE_BYTES.labels(
                method=method,
                endpoint=path
            ).observe(response_size)
            
            # Log request
            self.logger.info(
                "Request completed",
                extra={
                    "trace_id": trace_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "request_size_bytes": request_size,
                    "response_size_bytes": response_size
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
