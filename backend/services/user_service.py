from typing import Optional
from sqlalchemy.orm import Session
from models.user import User
from fastapi import HTTPException
from datetime import datetime

class UserService:
    @staticmethod
    def create_user(db: Session, email: str, tenant_id: int, auth_type: str) -> User:
        """Create a new user"""
        try:
            user = User(
                email=email,
                tenant_id=tenant_id,
                auth_type=auth_type,
                is_active=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_tenant_users(db: Session, tenant_id: int, skip: int = 0, limit: int = 100):
        """Get all users for a tenant"""
        return db.query(User).filter(
            User.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()

user_service = UserService() 