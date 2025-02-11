from fastapi import APIRouter, BackgroundTasks
from schemas.auth import TenantCreate, UserCreate
from services.signup_service import signup_service

router = APIRouter()

@router.post("/signup/tenant")
async def create_tenant_with_admin(
    tenant_data: TenantCreate,
    background_tasks: BackgroundTasks
):
    """Create a new tenant and admin user"""
    tenant, admin = await signup_service.create_tenant_with_admin(
        tenant_data,
        background_tasks
    )
    return {
        "tenant_id": tenant.id,
        "admin_user_id": admin.id,
        "message": "Tenant created successfully"
    }

@router.post("/signup/user")
async def create_user(user_data: UserCreate):
    """Create a new user in an existing tenant"""
    user = signup_service.create_user(user_data)
    return {
        "user_id": user.id,
        "message": "User created successfully"
    } 