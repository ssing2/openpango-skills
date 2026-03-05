"""
Configuration management for OpenPango GitHub App
"""

import os
from typing import Optional


class Config:
    """Configuration settings for GitHub App"""
    
    # GitHub App credentials
    GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID", "")
    GITHUB_APP_SECRET: str = os.getenv("GITHUB_APP_SECRET", "")
    GITHUB_PRIVATE_KEY: str = os.getenv("GITHUB_PRIVATE_KEY", "")
    
    # Webhook settings
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8000"))
    
    # OpenClaw integration
    OPENCLAW_API_URL: str = os.getenv("OPENCLAW_API_URL", "http://localhost:3000")
    OPENCLAW_API_KEY: str = os.getenv("OPENCLAW_API_KEY", "")
    
    # Safety settings
    PROTECTED_BRANCHES: list = ["main", "master", "develop"]
    ALLOWED_REPOS: Optional[list] = None  # None = all repos allowed
    
    # Task dispatch settings
    MAX_CONCURRENT_TASKS: int = 10
    TASK_TIMEOUT: int = 3600  # 1 hour
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [
            cls.GITHUB_APP_ID,
            cls.GITHUB_APP_SECRET,
            cls.WEBHOOK_SECRET,
            cls.GITHUB_PRIVATE_KEY
        ]
        
        if not all(required):
            missing = [
                k for k, v in {
                    "GITHUB_APP_ID": cls.GITHUB_APP_ID,
                    "GITHUB_APP_SECRET": cls.GITHUB_APP_SECRET,
                    "WEBHOOK_SECRET": cls.WEBHOOK_SECRET,
                    "GITHUB_PRIVATE_KEY": cls.GITHUB_PRIVATE_KEY
                }.items() if not v
            ]
            raise ValueError(f"Missing required configuration: {missing}")
        
        return True
