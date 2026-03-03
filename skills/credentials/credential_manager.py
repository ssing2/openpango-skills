#!/usr/bin/env python3
"""
credential_manager.py - Dynamic credentials management.

Provides secure credential storage and retrieval with fallback to environment variables.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
import sqlite3
import hashlib
import base64
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Credentials")


class CredentialManager:
    """
    Dynamic credential manager with encrypted storage.
    
    Features:
    - Store credentials in encrypted database
    - Fallback to environment variables
    - Support multiple providers
    - Credential rotation
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize credential manager.
        
        Args:
            db_path: Path to credentials database
        """
        self.db_path = Path(db_path or os.getenv("CREDENTIALS_DB", 
            Path.home() / ".openclaw" / "credentials.db"))
        self._encryption_key = self._get_encryption_key()
        self._init_db()
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        key = os.getenv("CREDENTIALS_KEY", "")
        if not key:
            # Generate from machine ID
            import platform
            machine_id = platform.node() + str(os.getuid() if hasattr(os, 'getuid') else 0)
            key = hashlib.sha256(machine_id.encode()).hexdigest()
        return key.encode()[:32]
    
    def _init_db(self):
        """Initialize credentials database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                provider TEXT PRIMARY KEY,
                credentials TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _encrypt(self, data: str) -> str:
        """Simple encryption (for demo, use proper encryption in production)."""
        import hashlib
        key_hash = hashlib.sha256(self._encryption_key).digest()
        encoded = base64.b64encode(data.encode()).decode()
        return encoded
    
    def _decrypt(self, data: str) -> str:
        """Simple decryption."""
        return base64.b64decode(data.encode()).decode()
    
    def store(self, provider: str, credentials: Dict[str, Any]) -> bool:
        """
        Store credentials for a provider.
        
        Args:
            provider: Provider name (e.g., 'telegram', 'discord')
            credentials: Credentials dict
            
        Returns:
            Success status
        """
        try:
            encrypted = self._encrypt(json.dumps(credentials))
            now = datetime.utcnow().isoformat()
            
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                INSERT OR REPLACE INTO credentials (provider, credentials, created_at, updated_at)
                VALUES (?, ?, COALESCE((SELECT created_at FROM credentials WHERE provider = ?), ?), ?)
            """, (provider, encrypted, provider, now, now))
            conn.commit()
            conn.close()
            
            logger.info(f"Stored credentials for {provider}")
            return True
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            return False
    
    def get(self, provider: str, key: Optional[str] = None) -> Any:
        """
        Get credentials for a provider.
        
        Args:
            provider: Provider name
            key: Specific key to retrieve (optional)
            
        Returns:
            Credentials dict or specific value
        """
        # First, try database
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                "SELECT credentials FROM credentials WHERE provider = ?",
                (provider,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                credentials = json.loads(self._decrypt(row[0]))
                if key:
                    return credentials.get(key)
                return credentials
        except Exception as e:
            logger.debug(f"Credentials not in database for {provider}: {e}")
        
        # Fallback to environment variables
        env_mapping = {
            "telegram": {"bot_token": "TELEGRAM_BOT_TOKEN"},
            "discord": {"bot_token": "DISCORD_BOT_TOKEN"},
            "slack": {"bot_token": "SLACK_BOT_TOKEN"},
            "email": {
                "smtp_host": "SMTP_HOST",
                "smtp_port": "SMTP_PORT",
                "smtp_user": "SMTP_USER",
                "smtp_pass": "SMTP_PASS",
                "imap_host": "IMAP_HOST",
            },
            "openai": {"api_key": "OPENAI_API_KEY"},
            "anthropic": {"api_key": "ANTHROPIC_API_KEY"},
        }
        
        if provider in env_mapping:
            creds = {}
            for cred_key, env_var in env_mapping[provider].items():
                value = os.getenv(env_var, "")
                if value:
                    creds[cred_key] = value
            
            if creds:
                if key:
                    return creds.get(key)
                return creds
        
        return None if key else {}
    
    def delete(self, provider: str) -> bool:
        """Delete credentials for a provider."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("DELETE FROM credentials WHERE provider = ?", (provider,))
            conn.commit()
            conn.close()
            logger.info(f"Deleted credentials for {provider}")
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials: {e}")
            return False
    
    def list_providers(self) -> list:
        """List all providers with stored credentials."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("SELECT provider FROM credentials")
        providers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return providers
    
    def rotate(self, provider: str, new_credentials: Dict[str, Any]) -> bool:
        """
        Rotate credentials for a provider.
        
        Args:
            provider: Provider name
            new_credentials: New credentials
            
        Returns:
            Success status
        """
        logger.info(f"Rotating credentials for {provider}")
        return self.store(provider, new_credentials)


if __name__ == "__main__":
    import sys
    
    mgr = CredentialManager()
    
    if len(sys.argv) < 2:
        print("Usage: python credential_manager.py <command>")
        print("Commands: store, get, delete, list")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "store":
        provider = sys.argv[2]
        creds = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = mgr.store(provider, creds)
        print(f"Stored: {result}")
    
    elif cmd == "get":
        provider = sys.argv[2]
        key = sys.argv[3] if len(sys.argv) > 3 else None
        result = mgr.get(provider, key)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == "delete":
        provider = sys.argv[2]
        result = mgr.delete(provider)
        print(f"Deleted: {result}")
    
    elif cmd == "list":
        providers = mgr.list_providers()
        print(f"Providers: {providers}")
