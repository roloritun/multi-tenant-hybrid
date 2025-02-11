from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from sqlalchemy.sql import func
from database import Base
import enum

class TenancyType(enum.Enum):
    SHARED = "shared"
    DEDICATED = "dedicated"
    ENTERPRISE = "enterprise"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    tenancy_type = Column(Enum(TenancyType), nullable=False)
    db_connection = Column(String, nullable=True)  # Only for dedicated/enterprise
    redis_config = Column(JSON, nullable=True)  # For dedicated/enterprise
    blob_storage_config = Column(JSON, nullable=True)  # For dedicated/enterprise
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True) 