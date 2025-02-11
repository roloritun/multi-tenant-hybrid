from typing import Dict
from datetime import datetime
import asyncio
from fastapi import HTTPException

class ResourceQuotas:
    def __init__(self):
        self.default_limits = {
            'storage_gb': 10,
            'redis_mb': 500,
            'api_calls_per_minute': 1000,
            'max_file_size_mb': 100
        }
        
        self.usage_cache = {}  # Cache for usage metrics
        
    async def check_quota(self, tenant_id: int, resource_type: str, amount: float):
        """Check if operation would exceed quota"""
        current_usage = await self.get_usage(tenant_id, resource_type)
        limit = await self.get_limit(tenant_id, resource_type)
        
        if current_usage + amount > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded for {resource_type}"
            )
            
    async def get_limit(self, tenant_id: int, resource_type: str) -> float:
        """Get resource limit for tenant"""
        # In production, fetch from database
        return self.default_limits.get(resource_type)
        
    async def get_usage(self, tenant_id: int, resource_type: str) -> float:
        """Get current resource usage"""
        cache_key = f"{tenant_id}:{resource_type}"
        
        if cache_key not in self.usage_cache:
            # In production, fetch from monitoring system
            self.usage_cache[cache_key] = 0
            
        return self.usage_cache[cache_key]
        
    async def update_usage(self, tenant_id: int, resource_type: str, amount: float):
        """Update resource usage"""
        cache_key = f"{tenant_id}:{resource_type}"
        current = self.usage_cache.get(cache_key, 0)
        self.usage_cache[cache_key] = current + amount

quotas = ResourceQuotas() 