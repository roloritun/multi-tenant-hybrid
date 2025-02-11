from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional
import jwt
from datetime import datetime, timedelta, UTC

class TenantSecurity:
    def __init__(self):
        self.api_key_header = APIKeyHeader(name="X-API-Key")
        self.jwt_secret = "your-secret-key"  # Use environment variable in production
        
    async def validate_tenant_access(
        self,
        tenant_id: int,
        token: str,
        required_scope: Optional[str] = None
    ) -> bool:
        """Validate tenant access permissions"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check if token is for correct tenant
            if payload.get("tenant_id") != tenant_id:
                return False
                
            # Check scope if required
            if required_scope:
                scopes = payload.get("scopes", [])
                if required_scope not in scopes:
                    return False
                    
            return True
            
        except jwt.InvalidTokenError:
            return False
            
    def generate_tenant_token(
        self,
        tenant_id: int,
        scopes: list[str],
        expires_delta: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate JWT token for tenant"""
        expires = datetime.now(UTC) + expires_delta
        
        payload = {
            "tenant_id": tenant_id,
            "scopes": scopes,
            "exp": expires
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

security = TenantSecurity() 