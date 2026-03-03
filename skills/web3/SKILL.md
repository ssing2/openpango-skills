---
name: web3
description: "Secure wallet management, transaction signing, token balances, and smart contract interaction for EVM-compatible chains."
version: "1.1.0"
user-invocable: true
metadata:
  capabilities:
    - web3/wallet
    - web3/transactions
    - web3/contracts
    - web3/balances
    - web3/dry-run
  author: "Antigravity (OpenPango Core)"
  license: "MIT"
---

# Web3 & Crypto Native Skill

Enables OpenPango agents to interact with blockchain networks natively. Agents
can check balances, send transactions, and call smart contracts on any
EVM-compatible chain (Ethereum, Polygon, Base, Arbitrum, etc).

## Modules

| Module | Class | Description |
|--------|-------|-------------|
| `wallet.py` | `Web3Agent` | Low-level wallet, token balances, contract calls (v1.0) |
| `crypto_manager.py` | `CryptoManager` | Secure transfer manager with mandatory dry-run gate (v1.1) |

---

## CryptoManager (v1.1) — Secure Transfer Flow

`CryptoManager` enforces a two-step **simulate → sign-off** flow before any
funds leave the wallet. A dry-run simulation must be performed and its ID
returned before a real transaction can be broadcast.

### Quick Start

```python
from skills.web3.crypto_manager import CryptoManager

manager = CryptoManager()

# 1. Query a balance
balance = manager.get_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
print(f"ETH: {balance['balance_eth']}")

# 2. REQUIRED: simulate before transferring
sim = manager.simulate_transfer(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount_eth=0.01,
)
print(f"Gas cost: {sim['gas_cost_eth']} ETH")
print(f"Sufficient funds: {sim['sufficient_funds']}")

# 3. Execute with explicit sign-off (only after reviewing simulation)
if sim["sufficient_funds"]:
    tx = manager.transfer_funds(
        from_address="0xYourAddress",
        to_address="0xRecipient",
        amount_eth=0.01,
        simulation_id=sim["simulation_id"],
        sign_off=True,
        dry_run=False,
    )
    print(f"TX Hash: {tx['tx_hash']}")

# 4. Read a smart contract (no sign-off required)
result = manager.read_contract_state(
    abi=[...],
    address="0xContractAddress",
    function="balanceOf",
    args=["0xSomeAddress"],
)
print(result["result"])
```

### ERC-20 Token Transfer

```python
# Check token balance
token_balance = manager.get_balance(
    address="0xYourAddress",
    token_address="0xUSDC_Contract",
)

# Simulate token transfer
sim = manager.simulate_transfer(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount_eth=100.0,             # token units (not ETH)
    token_address="0xUSDC_Contract",
)

# Execute
tx = manager.transfer_funds(
    from_address="0xYourAddress",
    to_address="0xRecipient",
    amount_eth=100.0,
    token_address="0xUSDC_Contract",
    simulation_id=sim["simulation_id"],
    sign_off=True,
    dry_run=False,
)
```

### API Reference

#### `get_balance(address, token_address=None)`

Returns ETH or ERC-20 token balance.

| Field | Type | Description |
|-------|------|-------------|
| `balance_eth` | float | Native ETH balance |
| `balance_wei` | int | Balance in wei |
| `balance_token` | float | Token balance (when token_address provided) |
| `chain_id` | int | Chain ID |
| `mock` | bool | Whether running in mock mode |

#### `simulate_transfer(from_address, to_address, amount_eth, token_address=None)`

Dry-runs the transfer. **Must be called before `transfer_funds`**.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | str | Pass this to `transfer_funds` |
| `estimated_gas` | int | Gas units estimated |
| `gas_cost_eth` | float | Cost in ETH |
| `net_cost_eth` | float | Total ETH needed (amount + gas) |
| `sufficient_funds` | bool | Whether the sender can afford it |
| `warnings` | list | Any high-gas or balance warnings |

#### `transfer_funds(from_address, to_address, amount_eth, ..., simulation_id, sign_off, dry_run=True)`

Broadcasts a transaction. Requires a valid `simulation_id` and `sign_off=True`.
`dry_run=True` (the default) returns a simulation without sending.

#### `read_contract_state(abi, address, function, args=None)`

Calls a read-only (`view`/`pure`) smart contract function. No signing required.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `WEB3_RPC_URL` | Yes (live mode) | HTTP/WebSocket RPC endpoint |
| `AGENT_WALLET_PRIVATE_KEY` | Yes (transfers) | Hex private key (`0x…`) |
| `WEB3_CHAIN_ID` | No | Chain ID (default: `1` = Ethereum mainnet) |

> **Security**: Private keys are read exclusively from environment variables.
> They must never be hardcoded or passed as function arguments.

## Mock Mode

When `WEB3_RPC_URL` is not set (or `web3` is not installed), all operations
run in mock mode with simulated balances. This enables offline unit-testing
and CI pipelines without a live node.

## Supported Chains

Any EVM-compatible chain: Ethereum, Polygon, Base, Arbitrum, Optimism, BSC,
Avalanche C-Chain, etc. Set `WEB3_CHAIN_ID` and `WEB3_RPC_URL` accordingly.
