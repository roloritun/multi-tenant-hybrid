from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from backend.models.tenant import Tenant
from backend.schemas.auth import TenantCreate
from backend.services.tenant_resources import tenant_resources
from backend.database import db_manager
from backend.services.tenant_resources import create_tenant_database

router = APIRouter()

@router.post("/tenants")
async def create_tenant(tenant_data: TenantCreate):
    try:
        with db_manager.get_db() as db:
            # Create tenant in shared DB
            new_tenant = Tenant(
                name=tenant_data.name,
                db_type=tenant_data.db_type
            )
            
            if tenant_data.db_type == 'dedicated':
                # Create new database for tenant
                db_name = f"tenant_{tenant_data.name.lower()}"
                connection_string = f"postgresql://user:pass@localhost/{db_name}"
                new_tenant.db_connection = connection_string
                
                # Create dedicated resources
                resources = await tenant_resources.create_tenant_resources(tenant_data.name)
                new_tenant.redis_config = resources['redis_config']
                new_tenant.blob_storage_config = resources['blob_storage_config']
                
                # Create new database and initialize schema
                await create_tenant_database(db_name)
                
            db.add(new_tenant)
            db.commit()
            db.refresh(new_tenant)
            
            return new_tenant
            
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e)) 