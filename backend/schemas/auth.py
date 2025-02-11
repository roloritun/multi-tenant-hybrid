from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class TenantCreate(BaseModel):
    name: str
    db_type: Literal['shared', 'dedicated']
    admin_email: EmailStr
    admin_first_name: str
    admin_last_name: str

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    tenant_id: int 