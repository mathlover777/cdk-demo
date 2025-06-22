import os
from typing import Any
from dotenv import load_dotenv

class Config:
    def __init__(self, stage: str):
        self.stage = stage
        self._load_config()
    
    def _load_config(self):
        """Load configuration from base and stage-specific env files"""
        # Load base configuration
        base_env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'env.base')
        if os.path.exists(base_env_path):
            load_dotenv(base_env_path)
        
        # Load stage-specific configuration (overrides base)
        stage_env_path = os.path.join(os.path.dirname(__file__), '..', '..', f'env.{self.stage}')
        if os.path.exists(stage_env_path):
            load_dotenv(stage_env_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value from environment variables"""
        return os.getenv(key, default)
    
    def get_domain_name(self) -> str:
        """Get the full domain name for the stage"""
        domain_name = self.get('DOMAIN_NAME')
        subdomain = self.get('SUBDOMAIN')
        return f"{subdomain}.{domain_name}" 