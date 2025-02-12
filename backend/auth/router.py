from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from google.oauth2 import id_token
from google.auth.transport import requests
from jose import JWTError, jwt
from datetime import datetime, timedelta, UTC
from backend.config.tenant_config import config_manager
from backend.services.user_service import user_service
from backend.database import db_manager
from typing import Optional
from sqlalchemy.orm import Session

router = APIRouter()

# JWT Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = db_manager.get_db_session()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/auth/google")
async def google_login(token: str, db: Session = Depends(get_db)):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), "YOUR_GOOGLE_CLIENT_ID"
        )
        
        # Get user
        user = user_service.get_user_by_email(db, idinfo['email'])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get tenant configuration
        tenant_config = config_manager.get_tenant_config(user.tenant)
        token_lifetime = tenant_config['security']['max_token_lifetime_hours']
        
        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.email,
                "tenant_id": user.tenant_id,
                "scopes": tenant_config['features']
            },
            expires_delta=timedelta(hours=token_lifetime)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "tenant_id": user.tenant_id,
            "features": tenant_config['features']
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")

@router.post("/auth/otp/send")
async def send_otp(email: str, db: Session = Depends(get_db)):
    # Get user
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tenant_config = config_manager.get_tenant_config(user.tenant)
    if not tenant_config['features'].get('otp_login', True):
        raise HTTPException(status_code=403, detail="OTP login not enabled")
    
    # Implement OTP generation and sending logic
    pass

@router.post("/auth/otp/verify")
async def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    # Get user
    user = user_service.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tenant_config = config_manager.get_tenant_config(user.tenant)
    token_lifetime = tenant_config['security']['max_token_lifetime_hours']
    
    # Verify OTP and create access token
    # ... OTP verification logic ...
    
    access_token = create_access_token(
        data={
            "sub": email,
            "tenant_id": user.tenant_id,
            "scopes": tenant_config['features']
        },
        expires_delta=timedelta(hours=token_lifetime)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "tenant_id": user.tenant_id,
        "features": tenant_config['features']
    } 