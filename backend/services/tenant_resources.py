from azure.storage.blob import BlobServiceClient
import redis
from typing import Dict
import json
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class TenantResourceManager:
    def __init__(self):
        # Shared resource configurations
        self.shared_redis_url = "redis://localhost:6379/0"
        self.shared_blob_connection = "DefaultEndpointsProtocol=https;AccountName=shared;..."
        
        # Cache for tenant connections
        self.redis_connections = {}
        self.blob_clients = {}

    async def create_tenant_resources(self, tenant_name: str) -> Dict:
        """Create dedicated resources for a new tenant"""
        
        # Create dedicated Redis database
        redis_config = await self.create_redis_instance(tenant_name)
        
        # Create dedicated Blob Storage container
        blob_config = await self.create_blob_storage(tenant_name)
        
        return {
            "redis_config": redis_config,
            "blob_storage_config": blob_config
        }

    async def create_redis_instance(self, tenant_name: str) -> Dict:
        """Create a dedicated Redis instance for the tenant"""
        # In production, you would use Azure Cache for Redis or similar
        # This is a simplified example
        redis_config = {
            "host": "localhost",
            "port": 6379,
            "db": self._get_next_redis_db(),  # Method to get next available Redis DB
            "tenant_name": tenant_name
        }
        return redis_config

    async def create_blob_storage(self, tenant_name: str) -> Dict:
        """Create dedicated blob storage for the tenant"""
        account_name = f"tenant{tenant_name.lower()}"
        # In production, you would create a new storage account or container
        blob_config = {
            "connection_string": f"DefaultEndpointsProtocol=https;AccountName={account_name};...",
            "container_name": "primary"
        }
        return blob_config

    def get_redis_connection(self, tenant):
        """Get Redis connection for a tenant"""
        if tenant.db_type == 'shared':
            return redis.from_url(self.shared_redis_url)

        if tenant.id not in self.redis_connections:
            config = tenant.redis_config
            self.redis_connections[tenant.id] = redis.Redis(
                host=config['host'],
                port=config['port'],
                db=config['db']
            )
        
        return self.redis_connections[tenant.id]

    def get_blob_client(self, tenant):
        """Get Blob Storage client for a tenant"""
        if tenant.db_type == 'shared':
            return BlobServiceClient.from_connection_string(self.shared_blob_connection)

        if tenant.id not in self.blob_clients:
            config = tenant.blob_storage_config
            self.blob_clients[tenant.id] = BlobServiceClient.from_connection_string(
                config['connection_string']
            )
        
        return self.blob_clients[tenant.id]

async def create_tenant_database(db_name: str):
    """Create a new database for the tenant."""
    try:
        # Create a new engine for the PostgreSQL server
        engine = create_engine("postgresql://user:pass@localhost/")
        
        # Connect to the PostgreSQL server
        with engine.connect() as connection:
            # Execute the SQL command to create a new database
            connection.execute(f"CREATE DATABASE {db_name};")
            
    except SQLAlchemyError as e:
        # Handle any errors that occur during the database creation
        raise Exception(f"Failed to create database {db_name}: {str(e)}")

tenant_resources = TenantResourceManager() 