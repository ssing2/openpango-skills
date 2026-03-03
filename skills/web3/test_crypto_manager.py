"""
test_crypto_manager.py — Unit tests for CryptoManager.

All tests run in mock mode (no live RPC or private key required).
Tests validate the mandatory dry-run gate, simulation ID flow,
balance queries, and contract reads.
"""

import os
import sys
import unittest

# Ensure package root is on path when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from skills.web3.crypto_manager import CryptoManager

_ADDR_A = "0x" + "aa" * 20
_ADDR_B = "0x" + "bb" * 20
_TOKEN  = "0x" + "cc" * 20


class TestCryptoManagerMockMode(unittest.TestCase):
    """All tests run in mock mode — no live RPC needed."""

    def setUp(self) -> None:
        os.environ.pop("WEB3_RPC_URL", None)
        os.environ.pop("AGENT_WALLET_PRIVATE_KEY", None)
        self.cm = CryptoManager()

    # ------------------------------------------------------------------ #
    # Mock mode initialisation                                             #
    # ------------------------------------------------------------------ #

    def test_mock_mode_active(self) -> None:
        self.assertTrue(self.cm._mock)

    def test_mock_address_generated(self) -> None:
        self.assertTrue(self.cm._mock_address.startswith("0x"))
        self.assertEqual(len(self.cm._mock_address), 42)

    # ------------------------------------------------------------------ #
    # Tool 1 — get_balance                                                 #
    # ------------------------------------------------------------------ #

    def test_get_balance_known_address(self) -> None:
        addr = self.cm._mock_address
        result = self.cm.get_balance(addr)
        self.assertIn("balance_eth", result)
        self.assertEqual(result["balance_eth"], 10.0)
        self.assertTrue(result["mock"])

    def test_get_balance_unknown_address(self) -> None:
        result = self.cm.get_balance(_ADDR_A)
        self.assertEqual(result["balance_eth"], 0.0)

    def test_get_balance_erc20_token(self) -> None:
        result = self.cm.get_balance(_ADDR_A, token_address=_TOKEN)
        self.assertIn("balance_token", result)
        self.assertEqual(result["token_address"], _TOKEN)
        self.assertTrue(result["mock"])

    # ------------------------------------------------------------------ #
    # Tool 2 — simulate_transfer                                           #
    # ------------------------------------------------------------------ #

    def test_simulate_transfer_returns_simulation_id(self) -> None:
        sim = self.cm.simulate_transfer(_ADDR_A, _ADDR_B, 0.1)
        self.assertIn("simulation_id", sim)
        self.assertTrue(sim["simulation_id"].startswith("sim_"))

    def test_simulate_transfer_insufficient_funds(self) -> None:
        sim = self.cm.simulate_transfer(_ADDR_A, _ADDR_B, 999.0)
        self.assertFalse(sim["sufficient_funds"])
        self.assertTrue(len(sim["warnings"]) > 0)

    def test_simulate_transfer_sufficient_funds(self) -> None:
        addr = self.cm._mock_address
        sim = self.cm.simulate_transfer(addr, _ADDR_B, 1.0)
        self.assertTrue(sim["sufficient_funds"])
        self.assertEqual(sim["warnings"], [])

    def test_simulate_registers_pending(self) -> None:
        sim = self.cm.simulate_transfer(_ADDR_A, _ADDR_B, 0.5)
        sim_id = sim["simulation_id"]
        self.assertIn(sim_id, self.cm._pending_simulations)

    # ------------------------------------------------------------------ #
    # Tool 2 — transfer_funds gate enforcement                             #
    # ------------------------------------------------------------------ #

    def test_transfer_without_sign_off_returns_simulation(self) -> None:
        """transfer_funds with dry_run=True (default) must not send a tx."""
        result = self.cm.transfer_funds(
            from_address=self.cm._mock_address,
            to_address=_ADDR_B,
            amount_eth=0.1,
            dry_run=True,
        )
        # Should return simulation dict, not a tx hash
        self.assertIn("simulation_id", result)
        self.assertNotIn("tx_hash", result)

    def test_transfer_sign_off_false_returns_simulation(self) -> None:
        result = self.cm.transfer_funds(
            from_address=self.cm._mock_address,
            to_address=_ADDR_B,
            amount_eth=0.1,
            sign_off=False,
            dry_run=False,
        )
        self.assertIn("simulation_id", result)
        self.assertNotIn("tx_hash", result)

    def test_transfer_without_simulation_id_errors(self) -> None:
        result = self.cm.transfer_funds(
            from_address=self.cm._mock_address,
            to_address=_ADDR_B,
            amount_eth=0.1,
            simulation_id=None,
            sign_off=True,
            dry_run=False,
        )
        self.assertIn("error", result)
        self.assertIn("simulation_id", result["error"].lower())

    def test_transfer_unknown_simulation_id_errors(self) -> None:
        result = self.cm.transfer_funds(
            from_address=self.cm._mock_address,
            to_address=_ADDR_B,
            amount_eth=0.1,
            simulation_id="sim_nonexistent",
            sign_off=True,
            dry_run=False,
        )
        self.assertIn("error", result)

    def test_transfer_full_flow_success(self) -> None:
        """Complete dry-run → sign-off flow must produce a tx hash."""
        sender = self.cm._mock_address
        initial_bal = self.cm._mock_balances[sender]

        sim = self.cm.simulate_transfer(sender, _ADDR_B, 1.0)
        self.assertTrue(sim["sufficient_funds"])

        tx = self.cm.transfer_funds(
            from_address=sender,
            to_address=_ADDR_B,
            amount_eth=1.0,
            simulation_id=sim["simulation_id"],
            sign_off=True,
            dry_run=False,
        )

        self.assertIn("tx_hash", tx)
        self.assertTrue(tx["tx_hash"].startswith("0x"))
        self.assertEqual(tx["status"], "confirmed")
        self.assertTrue(tx["mock"])
        # Balance should have decreased
        self.assertEqual(self.cm._mock_balances[sender], initial_bal - 1.0)

    def test_transfer_consumes_simulation(self) -> None:
        """After a successful transfer, the simulation_id is invalidated."""
        sender = self.cm._mock_address
        sim = self.cm.simulate_transfer(sender, _ADDR_B, 0.5)
        sim_id = sim["simulation_id"]

        self.cm.transfer_funds(
            from_address=sender,
            to_address=_ADDR_B,
            amount_eth=0.5,
            simulation_id=sim_id,
            sign_off=True,
            dry_run=False,
        )
        # Simulation should be gone
        self.assertNotIn(sim_id, self.cm._pending_simulations)

    def test_transfer_parameter_mismatch_errors(self) -> None:
        """Attempting transfer with mismatched params (different amount) fails."""
        sender = self.cm._mock_address
        sim = self.cm.simulate_transfer(sender, _ADDR_B, 0.5)

        result = self.cm.transfer_funds(
            from_address=sender,
            to_address=_ADDR_B,
            amount_eth=0.9,  # different amount!
            simulation_id=sim["simulation_id"],
            sign_off=True,
            dry_run=False,
        )
        self.assertIn("error", result)
        self.assertIn("not match", result["error"])

    def test_transfer_insufficient_funds_blocked(self) -> None:
        sender = self.cm._mock_address
        sim = self.cm.simulate_transfer(sender, _ADDR_B, 9999.0)
        self.assertFalse(sim["sufficient_funds"])

        result = self.cm.transfer_funds(
            from_address=sender,
            to_address=_ADDR_B,
            amount_eth=9999.0,
            simulation_id=sim["simulation_id"],
            sign_off=True,
            dry_run=False,
        )
        self.assertIn("error", result)
        self.assertIn("insufficient", result["error"].lower())

    # ------------------------------------------------------------------ #
    # Tool 3 — read_contract_state                                         #
    # ------------------------------------------------------------------ #

    def test_read_contract_state_mock(self) -> None:
        result = self.cm.read_contract_state(
            abi=[],
            address=_TOKEN,
            function="totalSupply",
        )
        self.assertEqual(result["function"], "totalSupply")
        self.assertEqual(result["args"], [])
        self.assertIn("result", result)
        self.assertTrue(result["mock"])

    def test_read_contract_state_with_args(self) -> None:
        result = self.cm.read_contract_state(
            abi=[],
            address=_TOKEN,
            function="balanceOf",
            args=[_ADDR_A],
        )
        self.assertEqual(result["function"], "balanceOf")
        self.assertEqual(result["args"], [_ADDR_A])
        self.assertTrue(result["mock"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
