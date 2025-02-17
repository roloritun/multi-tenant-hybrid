import logging
from contextlib import contextmanager
from typing import Dict, Optional, Generator

import redis
from redis import ConnectionPool
from backend.models.tenant import TenancyType
from database import db_manager

logger = logging.getLogger(__name__)


class RedisManager:
    def __init__(self):
        self.shared_redis_url = "redis://localhost:6379/0"
        self.tenant_pools: Dict[int, ConnectionPool] = {}
        self.shared_pool: Optional[ConnectionPool] = None
        self.shared_client: Optional[redis.Redis] = None

    def initialize(self):
        """Initialize shared Redis connection pool."""
        self.shared_pool = ConnectionPool.from_url(
            self.shared_redis_url,
            max_connections=10,
            decode_responses=True
        )
        self.shared_client = redis.Redis(connection_pool=self.shared_pool)

    def _create_pool(self, url: str) -> ConnectionPool:
        """Create a new Redis connection pool."""
        return ConnectionPool.from_url(
            url,
            max_connections=5,
            decode_responses=True
        )

    def get_redis_client(self, tenant_id: Optional[int] = None) -> redis.Redis:
        """Get Redis client for tenant or shared Redis."""
        try:
            if not tenant_id:
                return self.shared_client

            # Get tenant info from shared DB.
            tenant = db_manager.get_db()

            if tenant.tenancy_type == TenancyType.SHARED:
                return self.shared_client

            # Handle dedicated Redis.
            if tenant_id not in self.tenant_pools:
                if not tenant.redis_url:
                    raise ValueError(f"No Redis URL for tenant {tenant_id}")

                pool = self._create_pool(tenant.redis_url)
                self.tenant_pools[tenant_id] = pool

            return redis.Redis(connection_pool=self.tenant_pools[tenant_id])

        except Exception as e:
            logger.error(f"Error getting Redis client: {str(e)}")
            raise

    @contextmanager
    def get_redis(self, tenant_id: Optional[int] = None) -> Generator[redis.Redis, None, None]:
        """Context manager for Redis connections."""
        client = None
        try:
            client = self.get_redis_client(tenant_id)
            yield client
        except Exception as e:
            logger.error(f"Redis error: {str(e)}")
            raise
        finally:
            # Connection pools handle their own recycling in redis-py.
            pass

    def cleanup_tenant(self, tenant_id: int):
        """Clean up Redis connections for a tenant."""
        try:
            if tenant_id in self.tenant_pools:
                pool = self.tenant_pools.pop(tenant_id)
                pool.disconnect()
                logger.info(f"Cleaned up Redis connections for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Error cleaning up tenant Redis: {str(e)}")

    def cleanup_redis_connections(self):
        """Cleanup all Redis connections on shutdown."""
        try:
            # Clean shared connection.
            if self.shared_pool:
                self.shared_pool.disconnect()
                self.shared_pool = None
                self.shared_client = None

            # Clean tenant connections.
            for pool in self.tenant_pools.values():
                pool.disconnect()
            self.tenant_pools.clear()

            logger.info("Disposed all Redis connections")
        except Exception as e:
            logger.error(f"Error disposing Redis connections: {str(e)}")

    def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            # Check shared Redis.
            if not self.shared_client.ping():
                return False

            # Check tenant Redis instances.
            for tenant_id in self.tenant_pools:
                client = redis.Redis(connection_pool=self.tenant_pools[tenant_id])
                if not client.ping():
                    return False

            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False


# Global instance (initialize during app startup)
redis_manager = RedisManager()
