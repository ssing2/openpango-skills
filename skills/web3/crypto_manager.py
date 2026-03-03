#!/usr/bin/env python3
"""
crypto_manager.py — Web3 Crypto Manager Skill for OpenPango Agents.

Provides secure wallet operations, ERC-20 token transfers, and EVM smart
contract interaction. Private keys are read exclusively from environment
variables; they are never passed as function arguments or hardcoded.

Design principles
-----------------
* All state-changing operations (transfer_funds) are guarded by a mandatory
  dry-run phase.  The caller must obtain a ``simulation_id`` from
  ``simulate_transfer`` and pass it back with ``sign_off=True`` before any
  real transaction is broadcast.
* Private key material is read *once* at initialisation and never stored as a
  plain attribute accessible from outside the instance.
* Falls back to **mock mode** when ``WEB3_RPC_URL`` is not set, enabling
  offline unit-testing without a live node.

Environment variables
---------------------
WEB3_RPC_URL              HTTP/WebSocket RPC endpoint (e.g. Alchemy, Infura)
AGENT_WALLET_PRIVATE_KEY  Hex private key for the signing account (0x…)
WEB3_CHAIN_ID             Numeric chain ID (default: 1 = Ethereum mainnet)
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import time
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("CryptoManager")

# ---------------------------------------------------------------------------
# Optional web3 import — graceful degradation to mock mode
# ---------------------------------------------------------------------------
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    from eth_account import Account

    _WEB3_AVAILABLE = True
except ImportError:  # pragma: no cover — only missing in test envs without web3
    _WEB3_AVAILABLE = False
    logger.warning("web3 package not installed. Running in mock mode only.")


# ERC-20 minimal ABI: balanceOf + transfer
_ERC20_ABI: List[Dict] = [
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "_owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
    {
        "name": "transfer",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
]


class CryptoManager:
    """
    Secure Web3 crypto manager for OpenPango agents.

    Supports any EVM-compatible chain. When ``WEB3_RPC_URL`` is unset the
    instance runs in mock mode so that skills and tests work without a live
    node.

    Usage
    -----
    .. code-block:: python

        manager = CryptoManager()

        # 1. Check a balance
        bal = manager.get_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        # 2. Dry-run a transfer FIRST — required before any real send
        sim = manager.simulate_transfer(
            from_address="0xYourAddress",
            to_address="0xRecipient",
            amount_eth=0.01,
        )
        print(sim["simulation_id"])  # save this

        # 3. Execute with explicit sign-off
        tx = manager.transfer_funds(
            from_address="0xYourAddress",
            to_address="0xRecipient",
            amount_eth=0.01,
            simulation_id=sim["simulation_id"],
            sign_off=True,
        )
    """

    def __init__(self) -> None:
        rpc_url: str = os.getenv("WEB3_RPC_URL", "")
        self._chain_id: int = int(os.getenv("WEB3_CHAIN_ID", "1"))
        self._mock: bool = not bool(rpc_url) or not _WEB3_AVAILABLE

        # Pending simulations: simulation_id -> metadata
        self._pending_simulations: Dict[str, Dict] = {}

        if self._mock:
            logger.warning(
                "WEB3_RPC_URL not set or web3 unavailable. Running in MOCK mode."
            )
            _raw = "0x" + secrets.token_hex(20)
            self._mock_address: str = self._checksum(_raw)
            self._mock_balances: Dict[str, float] = {self._mock_address: 10.0}
            self._mock_nonce: int = 0
            self._mock_txs: List[Dict] = []
            self._w3 = None
            self._account = None
        else:
            logger.info(
                f"Connecting to RPC: {rpc_url[:40]}… (Chain ID: {self._chain_id})"
            )
            self._w3 = Web3(Web3.HTTPProvider(rpc_url))
            # Inject PoA middleware for chains like Polygon, BSC, Clique testnets
            self._w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

            raw_key: str = os.getenv("AGENT_WALLET_PRIVATE_KEY", "")
            if raw_key:
                # Normalise: ensure leading 0x
                if not raw_key.startswith("0x"):
                    raw_key = "0x" + raw_key
                self._account = Account.from_key(raw_key)
                logger.info(f"Loaded signing account: {self._account.address}")
            else:
                self._account = None
                logger.warning(
                    "AGENT_WALLET_PRIVATE_KEY not set. Read-only mode (no signing)."
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_signing(self) -> None:
        """Raise if no signing account is configured."""
        if self._account is None and not self._mock:
            raise RuntimeError(
                "No signing account configured. "
                "Set AGENT_WALLET_PRIVATE_KEY environment variable."
            )

    @staticmethod
    def _checksum(address: str) -> str:
        """Return EIP-55 checksummed address. Tolerant of bare hex input."""
        if _WEB3_AVAILABLE:
            return Web3.to_checksum_address(address)
        return address  # pass-through in mock-only mode

    @staticmethod
    def _make_simulation_id(*parts: Any) -> str:
        """Deterministic but unique simulation identifier."""
        digest_input = "-".join(str(p) for p in parts) + str(time.monotonic())
        return "sim_" + hashlib.sha256(digest_input.encode()).hexdigest()[:20]

    # ------------------------------------------------------------------
    # Tool 1: get_balance
    # ------------------------------------------------------------------

    def get_balance(
        self,
        address: str,
        token_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Return the native ETH (or token) balance for *address*.

        Parameters
        ----------
        address:
            EVM address to query (hex string, with or without 0x prefix).
        token_address:
            Optional ERC-20 contract address. When provided, returns the
            token balance instead of native ETH.

        Returns
        -------
        dict with keys: address, balance_eth (or balance_token), chain_id,
        mock (bool).
        """
        address = self._checksum(address)

        if self._mock:
            if token_address:
                return {
                    "address": address,
                    "token_address": token_address,
                    "balance_token": 1_000.0,
                    "decimals": 18,
                    "chain_id": self._chain_id,
                    "mock": True,
                }
            bal = self._mock_balances.get(address, 0.0)
            return {
                "address": address,
                "balance_eth": bal,
                "balance_wei": int(bal * 1e18),
                "chain_id": self._chain_id,
                "mock": True,
            }

        # Live mode
        assert self._w3 is not None
        if token_address:
            token_address = self._checksum(token_address)
            contract = self._w3.eth.contract(address=token_address, abi=_ERC20_ABI)
            decimals: int = contract.functions.decimals().call()
            raw_balance: int = contract.functions.balanceOf(address).call()
            human = raw_balance / (10**decimals)
            return {
                "address": address,
                "token_address": token_address,
                "balance_token": human,
                "balance_raw": raw_balance,
                "decimals": decimals,
                "chain_id": self._chain_id,
                "mock": False,
            }

        wei: int = self._w3.eth.get_balance(address)
        eth = self._w3.from_wei(wei, "ether")
        return {
            "address": address,
            "balance_eth": float(eth),
            "balance_wei": wei,
            "chain_id": self._chain_id,
            "mock": False,
        }

    # ------------------------------------------------------------------
    # Tool 2: transfer_funds — gated by mandatory dry-run
    # ------------------------------------------------------------------

    def simulate_transfer(
        self,
        from_address: str,
        to_address: str,
        amount_eth: float,
        token_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        **Required first step** before calling ``transfer_funds``.

        Simulates the transfer: checks balances, estimates gas, validates
        addresses, and issues a ``simulation_id`` that must be passed back
        with ``sign_off=True``.

        Parameters
        ----------
        from_address:   Sender address.
        to_address:     Recipient address.
        amount_eth:     Amount to send (in ETH, or token units if
                        *token_address* is provided).
        token_address:  Optional ERC-20 contract address for token transfers.

        Returns
        -------
        dict with simulation_id, estimated_gas, gas_cost_eth, net_cost_eth,
        sufficient_funds (bool), warnings.
        """
        from_address = self._checksum(from_address)
        to_address = self._checksum(to_address)

        sim_id = self._make_simulation_id(from_address, to_address, amount_eth)
        warnings: List[str] = []

        if self._mock:
            sender_balance = self._mock_balances.get(from_address, 0.0)
            gas_estimate = 65_000 if token_address else 21_000
            gas_price_gwei = 25.0
            gas_cost_eth = (gas_estimate * gas_price_gwei * 1e-9)
            net_cost = amount_eth + (0.0 if token_address else gas_cost_eth)
            sufficient = sender_balance >= net_cost

            if not sufficient:
                warnings.append(
                    f"Insufficient balance: need {net_cost:.6f} ETH, "
                    f"have {sender_balance:.6f} ETH"
                )

            result: Dict[str, Any] = {
                "simulation_id": sim_id,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "token_address": token_address,
                "estimated_gas": gas_estimate,
                "gas_price_gwei": gas_price_gwei,
                "gas_cost_eth": round(gas_cost_eth, 8),
                "net_cost_eth": round(net_cost, 8),
                "sender_balance_eth": sender_balance,
                "sufficient_funds": sufficient,
                "warnings": warnings,
                "chain_id": self._chain_id,
                "mock": True,
                "instructions": (
                    "To proceed, call transfer_funds() with this simulation_id "
                    "and sign_off=True."
                ),
            }
        else:
            # Live simulation
            assert self._w3 is not None
            balance_info = self.get_balance(from_address)
            sender_balance = balance_info["balance_eth"]

            gas_price_wei: int = self._w3.eth.gas_price
            gas_price_gwei = float(self._w3.from_wei(gas_price_wei, "gwei"))

            if token_address:
                gas_estimate = 70_000  # conservative ERC-20 estimate
            else:
                gas_estimate = self._w3.eth.estimate_gas(
                    {
                        "from": from_address,
                        "to": to_address,
                        "value": self._w3.to_wei(amount_eth, "ether"),
                    }
                )

            gas_cost_eth = float(
                self._w3.from_wei(gas_estimate * gas_price_wei, "ether")
            )
            net_cost = amount_eth + (0.0 if token_address else gas_cost_eth)
            sufficient = sender_balance >= net_cost

            if not sufficient:
                warnings.append(
                    f"Insufficient balance: need {net_cost:.6f} ETH, "
                    f"have {sender_balance:.6f} ETH"
                )
            if gas_price_gwei > 200:
                warnings.append(
                    f"High gas price detected: {gas_price_gwei:.1f} Gwei"
                )

            result = {
                "simulation_id": sim_id,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "token_address": token_address,
                "estimated_gas": gas_estimate,
                "gas_price_gwei": round(gas_price_gwei, 2),
                "gas_cost_eth": round(gas_cost_eth, 8),
                "net_cost_eth": round(net_cost, 8),
                "sender_balance_eth": sender_balance,
                "sufficient_funds": sufficient,
                "warnings": warnings,
                "chain_id": self._chain_id,
                "mock": False,
                "instructions": (
                    "To proceed, call transfer_funds() with this simulation_id "
                    "and sign_off=True."
                ),
            }

        # Register simulation so transfer_funds can validate it
        self._pending_simulations[sim_id] = {
            "from_address": from_address,
            "to_address": to_address,
            "amount_eth": amount_eth,
            "token_address": token_address,
            "sufficient_funds": result["sufficient_funds"],
        }
        logger.info(
            f"[SIM {sim_id}] {from_address[:10]}… → {to_address[:10]}… "
            f"| {amount_eth} ETH | sufficient={result['sufficient_funds']}"
        )
        return result

    def transfer_funds(
        self,
        from_address: str,
        to_address: str,
        amount_eth: float,
        token_address: Optional[str] = None,
        simulation_id: Optional[str] = None,
        sign_off: bool = False,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Transfer ETH or ERC-20 tokens between addresses.

        **You must call ``simulate_transfer`` first** and pass the returned
        ``simulation_id`` together with ``sign_off=True``.  Without a valid
        simulation_id and explicit sign-off the method refuses to proceed and
        returns the dry-run simulation instead.

        Parameters
        ----------
        from_address:    Sender (must match the simulation).
        to_address:      Recipient.
        amount_eth:      Amount in ETH (or token units for ERC-20).
        token_address:   Optional ERC-20 contract address.
        simulation_id:   ID obtained from ``simulate_transfer``.
        sign_off:        Must be ``True`` to broadcast the transaction.
        dry_run:         Kept for API compatibility. When ``True`` (default),
                         forces a simulation even if sign_off is set.

        Returns
        -------
        dict with tx hash, status, and transaction details.
        """
        from_address = self._checksum(from_address)
        to_address = self._checksum(to_address)

        # --- Safety gate: dry_run overrides sign_off ---
        if dry_run or not sign_off:
            logger.info(
                "[DRY-RUN] transfer_funds called without sign_off=True. "
                "Returning simulation only."
            )
            return self.simulate_transfer(from_address, to_address, amount_eth, token_address)

        # --- Validate simulation_id ---
        if simulation_id is None:
            return {
                "error": "simulation_id is required. Call simulate_transfer() first.",
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
            }

        sim = self._pending_simulations.get(simulation_id)
        if sim is None:
            return {
                "error": f"Unknown simulation_id: {simulation_id}. "
                         "Run simulate_transfer() to obtain a valid id.",
            }
        if not sim["sufficient_funds"]:
            return {
                "error": "Simulation indicated insufficient funds. Transfer aborted.",
                "simulation_id": simulation_id,
            }
        if (
            self._checksum(sim["from_address"]) != from_address
            or self._checksum(sim["to_address"]) != to_address
            or sim["amount_eth"] != amount_eth
        ):
            return {
                "error": "Transfer parameters do not match simulation. "
                         "Run a new simulate_transfer() for these parameters.",
            }

        # --- Execute ---
        self._require_signing()

        if self._mock:
            tx_hash = "0x" + secrets.token_hex(32)
            self._mock_nonce += 1
            self._mock_balances[from_address] = (
                self._mock_balances.get(from_address, 0.0) - amount_eth
            )
            self._mock_balances[to_address] = (
                self._mock_balances.get(to_address, 0.0) + amount_eth
            )
            tx_record: Dict[str, Any] = {
                "tx_hash": tx_hash,
                "from_address": from_address,
                "to_address": to_address,
                "amount_eth": amount_eth,
                "token_address": token_address,
                "nonce": self._mock_nonce,
                "chain_id": self._chain_id,
                "status": "confirmed",
                "simulation_id": simulation_id,
                "mock": True,
            }
            self._mock_txs.append(tx_record)
            # Consume simulation
            del self._pending_simulations[simulation_id]
            logger.info(
                f"[MOCK TX] {from_address[:10]}… → {to_address[:10]}… "
                f"| {amount_eth} ETH | {tx_hash[:18]}…"
            )
            return tx_record

        # Live mode
        assert self._w3 is not None and self._account is not None
        nonce: int = self._w3.eth.get_transaction_count(self._account.address)
        gas_price: int = self._w3.eth.gas_price

        if token_address:
            token_address = self._checksum(token_address)
            contract = self._w3.eth.contract(address=token_address, abi=_ERC20_ABI)
            decimals_val: int = contract.functions.decimals().call()
            raw_amount = int(amount_eth * (10**decimals_val))
            tx_params = contract.functions.transfer(to_address, raw_amount).build_transaction(
                {
                    "chainId": self._chain_id,
                    "gas": 70_000,
                    "gasPrice": gas_price,
                    "nonce": nonce,
                }
            )
        else:
            tx_params = {
                "chainId": self._chain_id,
                "to": to_address,
                "value": self._w3.to_wei(amount_eth, "ether"),
                "gas": 21_000,
                "gasPrice": gas_price,
                "nonce": nonce,
            }

        signed = self._account.sign_transaction(tx_params)
        tx_hash_bytes = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex: str = tx_hash_bytes.hex()

        logger.info(
            f"[TX BROADCAST] {from_address[:10]}… → {to_address[:10]}… "
            f"| {amount_eth} ETH | {tx_hash_hex[:18]}…"
        )

        del self._pending_simulations[simulation_id]
        return {
            "tx_hash": tx_hash_hex,
            "from_address": from_address,
            "to_address": to_address,
            "amount_eth": amount_eth,
            "token_address": token_address,
            "nonce": nonce,
            "chain_id": self._chain_id,
            "status": "broadcast",
            "simulation_id": simulation_id,
            "mock": False,
        }

    # ------------------------------------------------------------------
    # Tool 3: read_contract_state
    # ------------------------------------------------------------------

    def read_contract_state(
        self,
        abi: List[Dict],
        address: str,
        function: str,
        args: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call a read-only (``view`` / ``pure``) smart contract function.

        Parameters
        ----------
        abi:       Contract ABI as a Python list of dicts.
        address:   Deployed contract address.
        function:  Name of the function to call.
        args:      Positional arguments for the function (default: empty).

        Returns
        -------
        dict with contract, function, args, result, and mock flag.
        """
        address = self._checksum(address)
        args = args or []

        if self._mock:
            logger.info(f"[MOCK CONTRACT READ] {address[:12]}….{function}({args})")
            return {
                "contract": address,
                "function": function,
                "args": args,
                "result": f"mock_result_for_{function}",
                "chain_id": self._chain_id,
                "mock": True,
            }

        assert self._w3 is not None
        contract = self._w3.eth.contract(address=address, abi=abi)
        fn = contract.functions[function]
        result = fn(*args).call()
        logger.info(f"[CONTRACT READ] {address[:12]}….{function}({args}) → {result}")
        return {
            "contract": address,
            "function": function,
            "args": args,
            "result": result,
            "chain_id": self._chain_id,
            "mock": False,
        }
