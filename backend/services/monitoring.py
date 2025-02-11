from functools import wraps
import logging
from typing import Optional, Dict
import time

logger = logging.getLogger(__name__)

class TenantMetrics:
    def __init__(self):
        self.use_prometheus = False  # Set to True when you want to use Prometheus
        self._request_counts: Dict[str, int] = {}
        self._response_times: Dict[str, float] = {}
        
    def track_request(self):
        """Decorator to track API requests"""
        def decorator(func):
            @wraps(func)
            async def wrapper(request, *args, **kwargs):
                tenant_id = request.state.tenant_id
                path = request.url.path
                key = f"{tenant_id}:{path}"
                
                start_time = time.time()
                try:
                    result = await func(request, *args, **kwargs)
                    
                    # Update metrics
                    self._request_counts[key] = self._request_counts.get(key, 0) + 1
                    self._response_times[key] = time.time() - start_time
                    
                    # Log metrics
                    logger.info(f"Request metrics - tenant: {tenant_id}, path: {path}, "
                              f"duration: {self._response_times[key]:.3f}s")
                    
                    return result
                except Exception as e:
                    logger.error(f"Request failed - tenant: {tenant_id}, path: {path}, "
                               f"error: {str(e)}")
                    raise
            return wrapper
        return decorator
    
    def get_metrics(self, tenant_id: Optional[int] = None) -> Dict:
        """Get current metrics"""
        if tenant_id:
            return {
                "requests": {k: v for k, v in self._request_counts.items() 
                           if k.startswith(f"{tenant_id}:")},
                "response_times": {k: v for k, v in self._response_times.items() 
                                 if k.startswith(f"{tenant_id}:")}
            }
        return {
            "requests": self._request_counts,
            "response_times": self._response_times
        }

metrics = TenantMetrics() 