from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict
import yaml
import os
from backend.models.tenant import TenancyType


class TenantConfig(BaseSettings):
    config_path: str = Field(default="config/tenant_config.yaml")
    configs: Dict = Field(default_factory=dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_config()

    def load_config(self):
        """Load tenant configuration from YAML"""
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                self.configs = yaml.safe_load(f)

    def get_tenant_config(self, tenant) -> Dict:
        """Get configuration based on tenancy type"""
        base_config = self.configs.get("base", {})
        tenancy_config = self.configs.get(tenant.tenancy_type.value, {})

        # Merge base config with tenancy-specific config
        config = {**base_config}
        for key, value in tenancy_config.items():
            if isinstance(value, dict) and key in config:
                config[key] = {**config[key], **value}
            else:
                config[key] = value

        return config

    def get_resource_config(self, tenancy_type: TenancyType) -> Dict:
        """Get resource configuration for a tenancy type"""
        return self.configs.get(tenancy_type.value, {}).get("resources", {})


config_manager = TenantConfig()
