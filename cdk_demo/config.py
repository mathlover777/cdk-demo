import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    def __init__(self, stage: str):
        self.stage = stage
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from base and stage-specific env files"""
        config = {}
        
        # Load base configuration
        base_env_path = os.path.join(os.path.dirname(__file__), '..', 'env.base')
        if os.path.exists(base_env_path):
            load_dotenv(base_env_path)
            with open(base_env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
        
        # Load stage-specific configuration
        stage_env_path = os.path.join(os.path.dirname(__file__), '..', f'env.{self.stage}')
        if os.path.exists(stage_env_path):
            load_dotenv(stage_env_path)
            with open(stage_env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key] = value
        
        # Override with environment variables
        for key in config.keys():
            env_value = os.getenv(key)
            if env_value is not None:
                config[key] = env_value
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_domain_name(self) -> str:
        """Get the full domain name for the stage"""
        domain_name = self.get('DOMAIN_NAME')
        subdomain = self.get('SUBDOMAIN')
        return f"{subdomain}.{domain_name}"
    
    def get_stack_name(self) -> str:
        """Get the stack name"""
        return self.get('STACK_NAME', f"poc-backend-{self.stage}") 