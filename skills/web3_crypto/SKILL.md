---
name: web3_crypto
description: "Web3 and crypto native skill for wallet and blockchain operations."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - web3/wallet
    - web3/balance
    - web3/transfer
    - web3/sign
  author: "OpenPango Contributor"
  license: "MIT"
---

# Web3 & Crypto Native Skill

Blockchain wallet and transaction operations.

## Features

- **Wallet Management**: Create, import, export wallets
- **Balance Checking**: Multi-chain balance queries
- **Transaction Signing**: Sign messages and transactions
- **Token Operations**: ERC20 token interactions

## Supported Chains

- Ethereum / EVM chains
- Solana
- Base

## Usage

```python
from skills.web3_crypto.wallet import WalletManager

wallet = WalletManager()

# Check balance
balance = wallet.get_balance("0x...", chain="ethereum")

# Sign message
sig = wallet.sign_message("Hello")

# Transfer
tx = wallet.transfer("0x...", 1.0, chain="ethereum")
```
