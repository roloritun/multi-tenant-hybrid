from fastapi import APIRouter, Request, UploadFile, Depends, HTTPException
from backend.services.resource_quotas import quotas
from backend.services.monitoring import metrics
from backend.security.tenant_security import security
import json
from datetime import UTC, datetime
import logging

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload")
@metrics.track_request()
async def upload_file(
    request: Request,
    file: UploadFile,
    token: str = Depends(security.api_key_header)
):
    tenant_id = request.state.tenant_id
    
    # Validate tenant access
    if not await security.validate_tenant_access(tenant_id, token, "file:write"):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check file size quota
    file_size = len(await file.read())
    await file.seek(0)  # Reset file position
    
    await quotas.check_quota(
        tenant_id,
        "storage_gb",
        file_size / (1024 * 1024 * 1024)  # Convert to GB
    )
    
    # The middleware has already set up the correct blob client
    blob_client = request.state.blob_client
    container_client = blob_client.get_container_client("primary")
    
    try:
        # Upload file to tenant's storage
        blob_client = container_client.get_blob_client(file.filename)
        await blob_client.upload_blob(file.file)
        
        # Update usage metrics
        await quotas.update_usage(
            tenant_id,
            "storage_gb",
            file_size / (1024 * 1024 * 1024)
        )
        
        # Cache file metadata in tenant's Redis
        redis_client = request.state.redis
        metadata = {
            "size": file_size,
            "content_type": file.content_type,
            "uploaded_at": datetime.now(UTC).isoformat()
        }
        await redis_client.set(
            f"file:{file.filename}",
            json.dumps(metadata)
        )
        
        return {"status": "success"}
        
    except Exception as e:
        # Log error
        logger.error(f"Upload failed for tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed") 
