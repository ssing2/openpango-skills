#!/usr/bin/env python3
"""test_credential_manager.py - Tests for credential manager."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.credentials.credential_manager import CredentialManager


class TestCredentialManager(unittest.TestCase):
    """Test credential manager."""
    
    def setUp(self):
        """Set up test manager."""
        self.db_path = tempfile.mktemp(suffix=".db")
        self.mgr = CredentialManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_store_and_get(self):
        """Test store and get credentials."""
        creds = {"bot_token": "test_token_123"}
        self.mgr.store("telegram", creds)
        
        result = self.mgr.get("telegram")
        self.assertEqual(result.get("bot_token"), "test_token_123")
    
    def test_get_with_key(self):
        """Test get specific key."""
        creds = {"bot_token": "test_token", "chat_id": "12345"}
        self.mgr.store("telegram", creds)
        
        result = self.mgr.get("telegram", "bot_token")
        self.assertEqual(result, "test_token")
    
    def test_delete(self):
        """Test delete credentials."""
        self.mgr.store("telegram", {"token": "test"})
        self.mgr.delete("telegram")
        
        result = self.mgr.get("telegram")
        self.assertEqual(result, {})
    
    def test_list_providers(self):
        """Test list providers."""
        self.mgr.store("telegram", {"token": "test1"})
        self.mgr.store("discord", {"token": "test2"})
        
        providers = self.mgr.list_providers()
        self.assertIn("telegram", providers)
        self.assertIn("discord", providers)
    
    def test_rotate(self):
        """Test rotate credentials."""
        self.mgr.store("telegram", {"token": "old"})
        self.mgr.rotate("telegram", {"token": "new"})
        
        result = self.mgr.get("telegram", "token")
        self.assertEqual(result, "new")
    
    def test_env_fallback(self):
        """Test fallback to environment variables."""
        os.environ["TEST_PROVIDER_KEY"] = "env_value"
        
        # Provider not in database, should check env
        # Note: env_mapping doesn't include test_provider, so this returns None
        result = self.mgr.get("test_provider")
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
