"""
Webhook signature verification for GitHub events
"""

import hmac
import hashlib
from typing import Optional


class WebhookSignature:
    """Handle GitHub webhook signature verification"""
    
    @staticmethod
    def verify(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify GitHub webhook signature
        
        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value
            secret: Webhook secret configured in GitHub App
        
        Returns:
            bool: True if signature is valid
        
        Example:
            >>> payload = b'{"action": "opened"}'
            >>> signature = "sha256=abc123..."
            >>> secret = "my_webhook_secret"
            >>> WebhookSignature.verify(payload, signature, secret)
            True
        """
        if not signature or not secret:
            return False
        
        # GitHub sends signature as "sha256=<hash>"
        if not signature.startswith("sha256="):
            return False
        
        # Extract hash from signature
        provided_hash = signature[7:]  # Remove "sha256=" prefix
        
        # Calculate expected hash
        expected_hash = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_hash, provided_hash)
    
    @staticmethod
    def generate(payload: bytes, secret: str) -> str:
        """
        Generate webhook signature (for testing)
        
        Args:
            payload: Raw request body bytes
            secret: Webhook secret
        
        Returns:
            str: Signature in format "sha256=<hash>"
        """
        hash_value = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={hash_value}"
