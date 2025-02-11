from sqlalchemy.orm import Session
from models.tenant import Tenant, TenancyType
from models.user import User, UserRole
from schemas.auth import TenantCreate, UserCreate
from services.tenant_resources import tenant_resources
from services.email import send_welcome_email
from fastapi import HTTPException, BackgroundTasks
import logging

logger = logging.getLogger(__name__)

class SignupService:
    @staticmethod
    async def create_tenant_with_admin(
        db: Session,
        tenant_data: TenantCreate,
        background_tasks: BackgroundTasks
    ):
        """Create a new tenant with admin user"""
        try:
            # Create tenant
            new_tenant = Tenant(
                name=tenant_data.name,
                tenancy_type=tenant_data.tenancy_type
            )
            
            if tenant_data.tenancy_type in [TenancyType.DEDICATED, TenancyType.ENTERPRISE]:
                # Set up dedicated resources
                resources = await tenant_resources.create_tenant_resources(tenant_data.name)
                new_tenant.db_connection = resources['database']['connection_string']
                new_tenant.redis_config = resources['redis']
                new_tenant.blob_storage_config = resources['blob_storage']
            
            db.add(new_tenant)
            db.flush()  # Get tenant ID without committing
            
            # Create admin user
            admin_user = User(
                email=tenant_data.admin_email,
                first_name=tenant_data.admin_first_name,
                last_name=tenant_data.admin_last_name,
                tenant_id=new_tenant.id,
                role=UserRole.OWNER,  # First user is owner
                auth_type='google'
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(new_tenant)
            db.refresh(admin_user)
            
            # Send welcome email in background
            background_tasks.add_task(
                send_welcome_email,
                admin_user.email,
                admin_user.first_name,
                new_tenant.name
            )
            
            return new_tenant, admin_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating tenant with admin: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate):
        """Create a new user in an existing tenant"""
        try:
            # Verify tenant exists
            tenant = db.query(Tenant).filter_by(id=user_data.tenant_id).first()
            if not tenant:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            # Create user
            new_user = User(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                tenant_id=user_data.tenant_id,
                role=UserRole.STAFF,  # Default role for new users
                auth_type='google'
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            return new_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

signup_service = SignupService() 