import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pythonjsonlogger import jsonlogger

# Set up JSON logging for the backend
logger = logging.getLogger("netrestore.api")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class JSONLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Simple request logging
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info("Request processed", extra={
            "endpoint": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "latency_seconds": round(process_time, 3)
        })
        
        return response
