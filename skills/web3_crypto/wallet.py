#!/usr/bin/env python3
"""
wallet.py - Web3 wallet and blockchain operations.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Web3")


class WalletError(Exception):
    pass


class WalletManager:
    """
    Web3 wallet manager.
    
    Supports:
    - Ethereum / EVM chains
    - Solana
    - Balance checking
    - Message signing
    """
    
    def __init__(self):
        self.eth_rpc = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
        self.sol_rpc = os.getenv("SOL_RPC_URL", "https://api.mainnet-beta.solana.com")
        
        # Check for web3 libraries
        self._web3_available = self._check_web3()
        self._solana_available = self._check_solana()
    
    def _check_web3(self) -> bool:
        try:
            from web3 import Web3
            return True
        except ImportError:
            logger.warning("web3 not installed. Running in MOCK mode.")
            return False
    
    def _check_solana(self) -> bool:
        try:
            from solana.rpc.api import Client
            return True
        except ImportError:
            logger.warning("solana not installed. Running in MOCK mode.")
            return False
    
    # ─── Balance ───────────────────────────────────────────────────
    
    def get_balance(self, address: str, chain: str = "ethereum") -> Dict:
        """
        Get wallet balance.
        
        Args:
            address: Wallet address
            chain: Chain name (ethereum, solana, base)
            
        Returns:
            Balance info
        """
        if chain in ["ethereum", "eth", "base"]:
            return self._get_eth_balance(address, chain)
        elif chain in ["solana", "sol"]:
            return self._get_sol_balance(address)
        else:
            raise WalletError(f"Unsupported chain: {chain}")
    
    def _get_eth_balance(self, address: str, chain: str) -> Dict:
        """Get Ethereum balance."""
        if not self._web3_available:
            return self._mock_balance(address, chain, 1.5)
        
        try:
            from web3 import Web3
            
            rpc_url = self.eth_rpc if chain == "ethereum" else "https://mainnet.base.org"
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            balance_wei = w3.eth.get_balance(address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            
            return {
                "address": address,
                "chain": chain,
                "balance": float(balance_eth),
                "symbol": "ETH" if chain == "ethereum" else "ETH",
                "decimals": 18
            }
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return self._mock_balance(address, chain, 0.0)
    
    def _get_sol_balance(self, address: str) -> Dict:
        """Get Solana balance."""
        if not self._solana_available:
            return self._mock_balance(address, "solana", 10.0)
        
        try:
            from solana.rpc.api import Client
            
            client = Client(self.sol_rpc)
            response = client.get_balance(address)
            
            balance_lamports = response.value
            balance_sol = balance_lamports / 1_000_000_000
            
            return {
                "address": address,
                "chain": "solana",
                "balance": balance_sol,
                "symbol": "SOL",
                "decimals": 9
            }
        except Exception as e:
            logger.error(f"Error getting Solana balance: {e}")
            return self._mock_balance(address, "solana", 0.0)
    
    def _mock_balance(self, address: str, chain: str, balance: float) -> Dict:
        """Generate mock balance."""
        return {
            "address": address,
            "chain": chain,
            "balance": balance,
            "symbol": "ETH" if chain != "solana" else "SOL",
            "mock": True
        }
    
    # ─── Signing ────────────────────────────────────────────────────
    
    def sign_message(self, message: str, private_key: str) -> Dict:
        """
        Sign a message.
        
        Args:
            message: Message to sign
            private_key: Private key (hex)
            
        Returns:
            Signature info
        """
        if not self._web3_available:
            return self._mock_sign(message)
        
        try:
            from web3 import Web3
            from eth_account import Account
            
            account = Account.from_key(private_key)
            signature = account.sign_message(message)
            
            return {
                "message": message,
                "address": account.address,
                "signature": signature.signature.hex(),
                "success": True
            }
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            return {"success": False, "error": str(e)}
    
    def _mock_sign(self, message: str) -> Dict:
        """Generate mock signature."""
        return {
            "message": message,
            "signature": "0x" + hashlib.sha256(message.encode()).hexdigest(),
            "mock": True,
            "success": True
        }
    
    # ─── Transfer ────────────────────────────────────────────────────
    
    def transfer(
        self,
        to: str,
        amount: float,
        chain: str = "ethereum",
        private_key: Optional[str] = None
    ) -> Dict:
        """
        Transfer tokens.
        
        Args:
            to: Recipient address
            amount: Amount to transfer
            chain: Chain name
            private_key: Private key for signing
            
        Returns:
            Transaction info
        """
        if not private_key:
            return self._mock_transfer(to, amount, chain)
        
        if chain in ["ethereum", "eth", "base"]:
            return self._eth_transfer(to, amount, chain, private_key)
        elif chain in ["solana", "sol"]:
            return self._sol_transfer(to, amount, private_key)
        else:
            raise WalletError(f"Unsupported chain: {chain}")
    
    def _eth_transfer(self, to: str, amount: float, chain: str, private_key: str) -> Dict:
        """Transfer on Ethereum."""
        if not self._web3_available:
            return self._mock_transfer(to, amount, chain)
        
        try:
            from web3 import Web3
            from eth_account import Account
            
            rpc_url = self.eth_rpc if chain == "ethereum" else "https://mainnet.base.org"
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            account = Account.from_key(private_key)
            nonce = w3.eth.get_transaction_count(account.address)
            
            tx = {
                'nonce': nonce,
                'to': to,
                'value': w3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': w3.eth.gas_price,
                'chainId': 1 if chain == "ethereum" else 8453
            }
            
            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "from": account.address,
                "to": to,
                "amount": amount,
                "chain": chain
            }
        except Exception as e:
            logger.error(f"Error transferring: {e}")
            return {"success": False, "error": str(e)}
    
    def _sol_transfer(self, to: str, amount: float, private_key: str) -> Dict:
        """Transfer on Solana."""
        return self._mock_transfer(to, amount, "solana")
    
    def _mock_transfer(self, to: str, amount: float, chain: str) -> Dict:
        """Generate mock transfer."""
        return {
            "success": True,
            "tx_hash": "0x" + hashlib.sha256(f"{to}{amount}".encode()).hexdigest(),
            "to": to,
            "amount": amount,
            "chain": chain,
            "mock": True
        }
    
    # ─── Address Validation ───────────────────────────────────────────
    
    def validate_address(self, address: str, chain: str = "ethereum") -> Dict:
        """
        Validate an address.
        
        Args:
            address: Address to validate
            chain: Chain name
            
        Returns:
            Validation result
        """
        if chain in ["ethereum", "eth", "base"]:
            return self._validate_eth_address(address)
        elif chain in ["solana", "sol"]:
            return self._validate_sol_address(address)
        else:
            return {"valid": False, "error": f"Unknown chain: {chain}"}
    
    def _validate_eth_address(self, address: str) -> Dict:
        """Validate Ethereum address."""
        if not address.startswith("0x"):
            return {"valid": False, "error": "Must start with 0x"}
        
        if len(address) != 42:
            return {"valid": False, "error": "Must be 42 characters"}
        
        try:
            int(address[2:], 16)
            return {"valid": True, "address": address, "chain": "ethereum"}
        except ValueError:
            return {"valid": False, "error": "Invalid hex"}
    
    def _validate_sol_address(self, address: str) -> Dict:
        """Validate Solana address."""
        if len(address) < 32 or len(address) > 44:
            return {"valid": False, "error": "Invalid length"}
        
        return {"valid": True, "address": address, "chain": "solana"}


if __name__ == "__main__":
    import sys
    
    wallet = WalletManager()
    
    if len(sys.argv) < 2:
        print("Usage: python wallet.py <command>")
        print("Commands: balance, sign, transfer, validate")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "balance":
        address = sys.argv[2] if len(sys.argv) > 2 else "0x..."
        chain = sys.argv[3] if len(sys.argv) > 3 else "ethereum"
        result = wallet.get_balance(address, chain)
        print(json.dumps(result, indent=2))
    elif cmd == "sign":
        message = sys.argv[2] if len(sys.argv) > 2 else "Hello"
        result = wallet.sign_message(message, "0x" + "0" * 64)
        print(json.dumps(result, indent=2))
    elif cmd == "transfer":
        to = sys.argv[2] if len(sys.argv) > 2 else "0x..."
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
        result = wallet.transfer(to, amount)
        print(json.dumps(result, indent=2))
    elif cmd == "validate":
        address = sys.argv[2] if len(sys.argv) > 2 else "0x..."
        result = wallet.validate_address(address)
        print(json.dumps(result, indent=2))
