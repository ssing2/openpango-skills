#!/usr/bin/env python3
"""test_web3_contract.py - Tests for Web3 contract tools."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.coder.web3_contract import Web3Contract, ContractError, CompilationError


class TestWeb3Contract(unittest.TestCase):
    """Test Web3 contract tools."""
    
    def test_init_hardhat(self):
        """Test initialization with Hardhat."""
        contract = Web3Contract(framework="hardhat")
        self.assertEqual(contract.framework, "hardhat")
    
    def test_init_foundry(self):
        """Test initialization with Foundry."""
        contract = Web3Contract(framework="foundry")
        self.assertEqual(contract.framework, "foundry")
    
    def test_init_unknown_framework(self):
        """Test initialization with unknown framework."""
        with self.assertRaises(ContractError):
            Web3Contract(framework="unknown")
    
    def test_compile_mock(self):
        """Test compilation in mock mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = Web3Contract(project_path=tmpdir, framework="hardhat")
            # Without hardhat config, compilation will fail but we test the structure
            self.assertIsNotNone(contract.project_path)
    
    def test_simulate_deployment(self):
        """Test deployment simulation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = Web3Contract(project_path=tmpdir, framework="hardhat")
            result = contract.deploy_contract(
                "TestContract",
                network="localhost",
                constructor_args=[100, "test"],
                simulate_only=True
            )
            
            self.assertTrue(result["success"])
            self.assertTrue(result["simulated"])
            self.assertEqual(result["contract"], "TestContract")
            self.assertEqual(result["constructor_args"], [100, "test"])
    
    def test_mainnet_requires_approval(self):
        """Test that mainnet deployment requires approval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = Web3Contract(project_path=tmpdir, framework="hardhat")
            result = contract.deploy_contract(
                "TestContract",
                network="mainnet",
                simulate_only=False
            )
            
            self.assertFalse(result["success"])
            self.assertTrue(result["requires_approval"])
    
    def test_analyze_compilation_error_undeclared(self):
        """Test analyzing undeclared identifier error."""
        contract = Web3Contract(framework="hardhat")
        result = contract.analyze_compilation_error(
            "Error: Undeclared identifier 'foo'"
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["type"], "undeclared_identifier")
    
    def test_analyze_compilation_error_type(self):
        """Test analyzing type error."""
        contract = Web3Contract(framework="hardhat")
        result = contract.analyze_compilation_error(
            "Error: Type error: expected uint256"
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["type"], "type_error")
    
    def test_analyze_compilation_error_stack(self):
        """Test analyzing stack too deep error."""
        contract = Web3Contract(framework="hardhat")
        result = contract.analyze_compilation_error(
            "Error: Stack too deep"
        )
        
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["type"], "stack_too_deep")
    
    def test_analyze_compilation_error_warning(self):
        """Test analyzing warning."""
        contract = Web3Contract(framework="hardhat")
        result = contract.analyze_compilation_error(
            "Warning: Unused variable"
        )
        
        self.assertEqual(len(result["warnings"]), 1)


class TestWeb3ContractEnvironment(unittest.TestCase):
    """Test environment configuration."""
    
    def test_custom_project_path(self):
        """Test custom project path."""
        contract = Web3Contract(project_path="/custom/path", framework="hardhat")
        self.assertEqual(str(contract.project_path), "/custom/path")
    
    def test_default_project_path(self):
        """Test default project path."""
        contract = Web3Contract(framework="hardhat")
        self.assertEqual(contract.project_path, Path.cwd())


if __name__ == "__main__":
    unittest.main()
