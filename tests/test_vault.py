import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestration.router import VaultClient


class TestVaultClient(unittest.TestCase):
    @patch('orchestration.router.hvac')
    def test_vault_approle_auth(self, mock_hvac):
        """Test authentication via AppRole when ROLE_ID and SECRET_ID are set."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        with patch.dict(os.environ, {
            "VAULT_ADDR": "http://127.0.0.1:8200",
            "VAULT_ROLE_ID": "mock-role-id",
            "VAULT_SECRET_ID": "mock-secret-id",
        }, clear=True):
            vault = VaultClient()
            
            # Verify the client attempted AppRole login
            mock_client.auth.approle.login.assert_called_once_with(
                role_id="mock-role-id", secret_id="mock-secret-id"
            )
            self.assertIsNotNone(vault.client)

    @patch('orchestration.router.hvac')
    def test_vault_token_auth(self, mock_hvac):
        """Test authentication via Token when VAULT_TOKEN is set."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.Client.return_value = mock_client

        with patch.dict(os.environ, {
            "VAULT_TOKEN": "mock-vault-token",
        }, clear=True):
            vault = VaultClient()
            
            # Verify the client attempted Token auth
            self.assertEqual(mock_client.token, "mock-vault-token")
            self.assertIsNotNone(vault.client)

    @patch('orchestration.router.hvac')
    def test_get_secret_full(self, mock_hvac):
        """Test retrieving a full secret dictionary."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        
        # Mock the KV v2 read response
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'api_key': 'super-secret-key-123',
                    'username': 'admin'
                }
            }
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(os.environ, {"VAULT_TOKEN": "mock"}, clear=True):
            vault = VaultClient()
            result = vault.get_secret("openpango/twitter")
            
            self.assertEqual(result['api_key'], 'super-secret-key-123')
            self.assertEqual(result['username'], 'admin')

    @patch('orchestration.router.hvac')
    def test_get_secret_key_specific(self, mock_hvac):
        """Test retrieving a specific key from a secret payload."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        
        # Mock the KV v2 read response
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'api_key': 'expected-api-key',
                }
            }
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(os.environ, {"VAULT_TOKEN": "mock"}, clear=True):
            vault = VaultClient()
            result = vault.get_secret("openpango/twitter", key="api_key")
            
            self.assertEqual(result, 'expected-api-key')

if __name__ == '__main__':
    unittest.main()
