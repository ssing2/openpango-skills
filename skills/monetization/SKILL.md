---
name: "A2A Payment Router"
description: "Core monetization infrastructure enabling OpenPango agents to pay other agents using Fiat (Stripe) or Crypto (USDC/ETH)."
version: "1.0.0"
user-invocable: false
system-daemon: true
metadata:
  capabilities:
    - finance/fiat-transfer
    - finance/crypto-transfer
    - finance/escrow
  author: "Antigravity (OpenPango Core)"
  license: "MIT"
---

# A2A Payment Router & Wallet

The backbone of the OpenPango A2A (Agent-to-Agent) economy. This daemon allows an agent to attach a "bounty" to a sub-task and automatically release funds when the receiving agent provides proof of work.

## Setup

Requires valid API tokens exported to the environment:
- `STRIPE_API_KEY` (Test mode begins with `sk_test_`)
- `WEB3_RPC_URL` (Alchemy or Infura URL)
- `AGENT_WALLET_PRIVATE_KEY` (Hex string)

## Usage

```python
from skills.monetization.payment_router import PaymentRouter, Currency

wallet = PaymentRouter()

# 1. Lock funds in escrow for a task
escrow_id = wallet.lock_funds(
    amount=5.00, 
    currency=Currency.USD, 
    recipient_agent_id="agent-xyz-99",
    memo="Bounty for scraping protected site"
)

# 2. Upon task success, release the bounty
receipt = wallet.release_funds(escrow_id)
print(f"Funds transferred successfully! Tx Hash: {receipt['transaction_id']}")
```

## Features
- **Fiat Rails:** Stripe API integration.
- **Crypto Rails:** Web3.py integration for EVM chains (ETH, Polygon, Arbitrum) using USDC or native tokens.
- **Escrow Mechanics:** Prevents "runaway spending" by locking funds to specific task IDs.
