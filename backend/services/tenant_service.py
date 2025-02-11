from typing import Optional
from sqlalchemy.orm import Session
from models.tenant import Tenant, TenancyType
from services.tenant_resources import tenant_resources
from config.tenant_config import config_manager
from fastapi import HTTPException

class TenantService:
    @staticmethod
    async def create_tenant(db: Session, name: str, tenancy_type: TenancyType) -> Tenant:
        """Create a new tenant with specified tenancy type"""
        try:
            # Get resource configuration for tenancy type
            resource_config = config_manager.get_resource_config(tenancy_type)
            
            new_tenant = Tenant(
                name=name,
                tenancy_type=tenancy_type
            )
            
            if tenancy_type in [TenancyType.DEDICATED, TenancyType.ENTERPRISE]:
                # Create dedicated resources
                resources = await tenant_resources.create_tenant_resources(name)
                new_tenant.db_connection = resources['db_connection']
                new_tenant.redis_config = resources['redis_config']
                new_tenant.blob_storage_config = resources['blob_storage_config']
            
            db.add(new_tenant)
            db.commit()
            db.refresh(new_tenant)
            
            return new_tenant
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
        """Get tenant by ID"""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    @staticmethod
    def get_tenant_by_name(db: Session, name: str) -> Optional[Tenant]:
        """Get tenant by name"""
        return db.query(Tenant).filter(Tenant.name == name).first()
    
    @staticmethod
    async def update_tenant_status(db: Session, tenant_id: int, is_active: bool) -> Tenant:
        """Update tenant active status"""
        tenant = TenantService.get_tenant(db, tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.is_active = is_active
        db.commit()
        db.refresh(tenant)
        return tenant

tenant_service = TenantService() 