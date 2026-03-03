#!/usr/bin/env python3
"""test_wallet.py - Tests for wallet manager."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.web3_crypto.wallet import WalletManager, WalletError


class TestWalletManager(unittest.TestCase):
    """Test wallet manager."""
    
    def setUp(self):
        """Set up manager."""
        os.environ["ETH_RPC_URL"] = ""
        os.environ["SOL_RPC_URL"] = ""
        self.wallet = WalletManager()
    
    def test_mock_mode(self):
        """Test mock mode."""
        self.assertFalse(self.wallet._web3_available)
    
    def test_get_eth_balance_mock(self):
        """Test ETH balance in mock mode."""
        result = self.wallet.get_balance("0x" + "0" * 40, "ethereum")
        
        self.assertTrue(result["mock"])
        self.assertEqual(result["chain"], "ethereum")
    
    def test_get_sol_balance_mock(self):
        """Test SOL balance in mock mode."""
        result = self.wallet.get_balance("SolanaAddress123", "solana")
        
        self.assertTrue(result["mock"])
        self.assertEqual(result["chain"], "solana")
    
    def test_get_balance_invalid_chain(self):
        """Test invalid chain."""
        with self.assertRaises(WalletError):
            self.wallet.get_balance("address", "invalid")
    
    def test_sign_message_mock(self):
        """Test signing in mock mode."""
        result = self.wallet.sign_message("Hello", "0x" + "0" * 64)
        
        self.assertTrue(result["mock"])
    
    def test_transfer_mock(self):
        """Test transfer in mock mode."""
        result = self.wallet.transfer("0x" + "0" * 40, 1.0)
        
        self.assertTrue(result["mock"])
        self.assertTrue(result["success"])
    
    def test_validate_eth_address_valid(self):
        """Test valid ETH address."""
        result = self.wallet.validate_address("0x" + "0" * 40, "ethereum")
        
        self.assertTrue(result["valid"])
    
    def test_validate_eth_address_invalid_no_prefix(self):
        """Test ETH address without 0x."""
        result = self.wallet.validate_address("0" * 40, "ethereum")
        
        self.assertFalse(result["valid"])
    
    def test_validate_eth_address_invalid_length(self):
        """Test ETH address wrong length."""
        result = self.wallet.validate_address("0x" + "0" * 30, "ethereum")
        
        self.assertFalse(result["valid"])
    
    def test_validate_sol_address(self):
        """Test Solana address validation."""
        result = self.wallet.validate_address("SolanaAddress12345678901234567890", "solana")
        
        self.assertTrue(result["valid"])
    
    def test_validate_unknown_chain(self):
        """Test unknown chain validation."""
        result = self.wallet.validate_address("address", "unknown")
        
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
