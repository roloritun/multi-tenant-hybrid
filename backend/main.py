from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.database import db_manager
import logging
from backend.routers import files, tenant
from backend.auth import router as auth

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await db_manager.cleanup_db_connections()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    
    # Register routers
    app.include_router(auth.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(tenant.router, prefix="/api")
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 