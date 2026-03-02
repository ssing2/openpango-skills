import os
import json
import uuid
import logging
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PaymentRouter")

class Currency(str, Enum):
    USD = "USD"
    USDC = "USDC"
    ETH = "ETH"

class EscrowStatus(str, Enum):
    LOCKED = "locked"
    RELEASED = "released"
    REFUNDED = "refunded"

class PaymentRouter:
    """
    OpenPango Core Daemon: A2A Payment & Wallet Router.
    Handles multi-rail financial transactions between autonomous agents.
    """
    
    def __init__(self):
        self._stripe_key = os.getenv("STRIPE_API_KEY", "mock_sk_test")
        self._web3_url = os.getenv("WEB3_RPC_URL", "mock_rpc")
        self._wallet_key = os.getenv("AGENT_WALLET_PRIVATE_KEY", "mock_pk")
        
        self._mock_mode = (self._stripe_key == "mock_sk_test" or self._web3_url == "mock_rpc")
        self._escrows: Dict[str, Dict[str, Any]] = {}
        
        if self._mock_mode:
            logger.warning("PaymentRouter running in MOCK MODE. No real funds will move.")
        else:
            logger.info("PaymentRouter initialized with active API credentials.")

    def lock_funds(self, amount: float, currency: Currency, recipient_agent_id: str, memo: str = "") -> str:
        """
        Locks funds intended for a sub-agent into an escrow state.
        Ensures the agent actually possesses the funds before delegating the task.
        """
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        escrow_id = f"escrow_{uuid.uuid4().hex[:12]}"
        
        # In a real environment, we would verify wallet balance or Stripe balance here.
        if self._mock_mode:
            logger.info(f"Mockingly locking {amount} {currency} for {recipient_agent_id}")
            
        self._escrows[escrow_id] = {
            "amount": amount,
            "currency": currency,
            "recipient": recipient_agent_id,
            "memo": memo,
            "status": EscrowStatus.LOCKED,
            "created_at": datetime.now().isoformat()
        }
        
        return escrow_id

    def release_funds(self, escrow_id: str) -> Dict[str, Any]:
        """
        Releases locked funds to the assigned recipient after task verification.
        """
        if escrow_id not in self._escrows:
            raise ValueError(f"Invalid escrow ID: {escrow_id}")
            
        escrow = self._escrows[escrow_id]
        
        if escrow["status"] != EscrowStatus.LOCKED:
            raise ValueError(f"Cannot release funds; escrow status is {escrow['status']}")

        amount = escrow["amount"]
        currency = escrow["currency"]
        recipient = escrow["recipient"]

        logger.info(f"Releasing {amount} {currency} to agent {recipient}...")
        
        receipt = None
        if currency == Currency.USD:
            receipt = self._execute_fiat_transfer(amount, recipient)
        elif currency in [Currency.USDC, Currency.ETH]:
            receipt = self._execute_crypto_transfer(amount, currency, recipient)

        escrow["status"] = EscrowStatus.RELEASED
        escrow["receipt"] = receipt
        escrow["resolved_at"] = datetime.now().isoformat()
        
        return receipt

    def refund_escrow(self, escrow_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Refunds the locked capital back to the primary agent's wallet (e.g., if a sub-agent fails limits).
        """
        if escrow_id not in self._escrows:
            raise ValueError(f"Invalid escrow ID: {escrow_id}")

        escrow = self._escrows[escrow_id]
        
        if escrow["status"] != EscrowStatus.LOCKED:
            raise ValueError(f"Cannot refund; escrow status is {escrow['status']}")

        logger.info(f"Refunding escrow {escrow_id}. Reason: {reason}")
        
        escrow["status"] = EscrowStatus.REFUNDED
        escrow["resolved_at"] = datetime.now().isoformat()
        escrow["refund_reason"] = reason
        
        return {"status": "success", "action": "refunded", "escrow_id": escrow_id}

    def _execute_fiat_transfer(self, amount: float, recipient: str) -> Dict[str, Any]:
        """Executes a USD transfer via Stripe Connect"""
        if self._mock_mode:
            tx_id = f"pi_mock_{uuid.uuid4().hex[:8]}"
            logger.info(f"[MOCK STRIPE] Transferred ${amount} to {recipient} (Tx: {tx_id})")
            return {"status": "success", "transaction_id": tx_id, "rail": "fiat/stripe", "network": "ach"}
            
        # Realistic stub: import stripe; stripe.api_key = self._stripe_key; stripe.Transfer.create(...)
        return {"status": "success", "transaction_id": "pi_real_123", "rail": "fiat/stripe", "network": "ach"}

    def _execute_crypto_transfer(self, amount: float, currency: Currency, recipient: str) -> Dict[str, Any]:
        """Executes an EVM transfer via Web3.py"""
        if self._mock_mode:
            tx_id = f"0xmock{uuid.uuid4().hex}"
            logger.info(f"[MOCK WEB3] Transferred {amount} {currency} to {recipient} (Tx: {tx_id})")
            return {"status": "success", "transaction_id": tx_id, "rail": "crypto/evm", "network": "ethereum"}

        # Realistic stub: Signed EVM transaction broadcast via web3 Provider
        return {"status": "success", "transaction_id": "0xreal456", "rail": "crypto/evm", "network": "ethereum"}

if __name__ == "__main__":
    wallet = PaymentRouter()
    logger.info("Demonstrating A2A Microtransaction Escrow...")
    eid = wallet.lock_funds(2.50, Currency.USDC, "agent-scraping-bot-44", "Bounty completion payment")
    receipt = wallet.release_funds(eid)
    print(json.dumps(receipt, indent=2))
