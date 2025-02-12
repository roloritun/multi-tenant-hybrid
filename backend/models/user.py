from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from backend.base import Base
import enum

class UserRole(enum.Enum):
    OWNER = "owner"      # First user, full control
    ADMIN = "admin"      # Can manage users and settings
    STAFF = "staff"      # Regular user

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    role = Column(Enum(UserRole), nullable=False)
    auth_type = Column(String)  # 'google' or 'otp'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 