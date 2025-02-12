from sqlalchemy.orm import Session
from typing import Optional
from backend.models.tenant import Tenant, TenancyType
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    @staticmethod
    def get_tenant_session(db: Session, tenant_id: int) -> Optional[Tenant]:
        """Get tenant and validate session access"""
        try:
            tenant = db.query(Tenant).filter_by(id=tenant_id).first()
            if not tenant:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tenant {tenant_id} not found"
                )
            
            if not tenant.is_active:
                raise HTTPException(
                    status_code=403,
                    detail=f"Tenant {tenant_id} is inactive"
                )
            
            return tenant
            
        except Exception as e:
            logger.error(f"Error getting tenant session: {str(e)}")
            raise

    @staticmethod
    async def check_db_health(db: Session) -> bool:
        """Check database health"""
        try:
            db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

db_service = DatabaseService() 