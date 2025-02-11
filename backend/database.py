from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging
from models.tenant import Tenant, TenancyType
from services.db_service import db_service

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        # Load from environment variables in production
        self.shared_db_url = "postgresql://user:pass@localhost/shared_db"
        self.tenant_engines: Dict[int, Any] = {}
        self.tenant_sessions: Dict[int, sessionmaker] = {}
        
        # Create shared DB engine with connection pooling
        self.shared_engine = create_engine(
            self.shared_db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True
        )
        self.SharedSessionLocal = sessionmaker(
            bind=self.shared_engine,
            autocommit=False,
            autoflush=False
        )

    def _create_tenant_engine(self, connection_string: str):
        """Create a new database engine with connection pooling"""
        return create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=3,
            max_overflow=5,
            pool_timeout=30,
            pool_pre_ping=True
        )

    def get_db_session(self, tenant_id: Optional[int] = None):
        """Get database session for tenant or shared DB"""
        try:
            if not tenant_id:
                return self.SharedSessionLocal()
                
            # Get tenant info from shared DB
            with self.SharedSessionLocal() as shared_session:
                tenant = db_service.get_tenant_session(shared_session, tenant_id)
                
                if tenant.tenancy_type == TenancyType.SHARED:
                    return self.SharedSessionLocal()
                
                # Handle dedicated DB
                if tenant_id not in self.tenant_sessions:
                    if not tenant.db_connection:
                        raise ValueError(f"No database connection for tenant {tenant_id}")
                        
                    engine = self._create_tenant_engine(tenant.db_connection)
                    self.tenant_engines[tenant_id] = engine
                    self.tenant_sessions[tenant_id] = sessionmaker(
                        bind=engine,
                        autocommit=False,
                        autoflush=False
                    )
                
                return self.tenant_sessions[tenant_id]()
                
        except Exception as e:
            logger.error(f"Error getting database session: {str(e)}")
            raise

    @contextmanager
    def get_db(self, tenant_id: Optional[int] = None):
        """Context manager for database sessions"""
        db = None
        try:
            db = self.get_db_session(tenant_id)
            yield db
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if db:
                db.close()

    def cleanup_tenant(self, tenant_id: int):
        """Clean up database connections for a tenant"""
        try:
            if tenant_id in self.tenant_engines:
                self.tenant_engines[tenant_id].dispose()
                del self.tenant_engines[tenant_id]
                del self.tenant_sessions[tenant_id]
                logger.info(f"Cleaned up database connections for tenant {tenant_id}")
        except Exception as e:
            logger.error(f"Error cleaning up tenant connections: {str(e)}")

    async def cleanup_db_connections(self):
        """Cleanup database connections on shutdown"""
        try:
            # Dispose shared engine
            self.shared_engine.dispose()
            
            # Dispose tenant engines
            for engine in self.tenant_engines.values():
                engine.dispose()
            
            self.tenant_engines.clear()
            self.tenant_sessions.clear()
            
            logger.info("Disposed all database connections")
        except Exception as e:
            logger.error(f"Error disposing database connections: {str(e)}")

    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            # Check shared DB
            with self.get_db() as db:
                if not await db_service.check_db_health(db):
                    return False
            
            # Check tenant DBs
            for tenant_id in self.tenant_engines:
                with self.get_db(tenant_id) as db:
                    if not await db_service.check_db_health(db):
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

# Global instance
db_manager = DatabaseManager() 