from fastapi import Request, Depends
from models.tenant import Tenant
from services.tenant_resources import tenant_resources
from database import db_manager
from sqlalchemy.orm import Session

async def get_tenant_context(
    request: Request,
    db: Session = Depends(db_manager.get_db_session)
):
    """Middleware to set up tenant context"""
    
    # Get tenant_id from JWT token or request
    tenant_id = request.state.tenant_id
    
    if tenant_id:
        tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        
        # Set up connections for the request
        request.state.db = db_manager.get_db_session(tenant_id)
        request.state.redis = tenant_resources.get_redis_connection(tenant)
        request.state.blob_client = tenant_resources.get_blob_client(tenant)
    
    return request

# Add middleware in main.py instead 