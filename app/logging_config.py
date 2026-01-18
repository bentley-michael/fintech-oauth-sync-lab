import logging
import json
import sys
from datetime import timezone, datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "lineno": record.lineno,
        }
        
        # Add correlation ID if available in request context via ThreadLocal or contextvar
        # For simplicity, we assume correlation_id is passed in 'extra' dict if needed
        # or we rely on 'extra' fields merged in.
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
            
        if hasattr(record, "method"):
            log_obj["method"] = record.method

        if hasattr(record, "path_url"): # 'path' is reserved for file path
            log_obj["url"] = record.path_url

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    # Mute loud libraries if needed
    logging.getLogger("uvicorn.access").disabled = True # We might want our own access logs
