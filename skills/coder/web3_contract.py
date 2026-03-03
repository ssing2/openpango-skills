#!/usr/bin/env python3
"""
web3_contract.py - Smart contract deployment and testing with Hardhat/Foundry.

Provides tools for compiling, testing, and deploying Solidity/Vyper contracts.
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Web3Contract")


class ContractError(Exception):
    """Base exception for contract errors."""
    pass


class CompilationError(ContractError):
    """Contract compilation failed."""
    pass


class TestError(ContractError):
    """Contract test failed."""
    pass


class DeploymentError(ContractError):
    """Contract deployment failed."""
    pass


class Web3Contract:
    """
    Smart contract development tools for Hardhat/Foundry.
    
    Supports:
    - Solidity/Vyper compilation
    - Contract testing
    - Deployment simulation
    - Mainnet deployment with HITL approval
    """
    
    def __init__(
        self,
        project_path: Optional[str] = None,
        framework: str = "hardhat"
    ):
        """
        Initialize Web3 contract handler.
        
        Args:
            project_path: Path to Hardhat/Foundry project
            framework: "hardhat" or "foundry"
        """
        self.project_path = Path(project_path or os.getcwd())
        self.framework = framework
        self._check_framework()
    
    def _check_framework(self):
        """Check if framework is available."""
        if self.framework == "hardhat":
            self._check_hardhat()
        elif self.framework == "foundry":
            self._check_foundry()
        else:
            raise ContractError(f"Unknown framework: {self.framework}")
    
    def _check_hardhat(self):
        """Check if Hardhat is available."""
        hardhat_config = self.project_path / "hardhat.config.js"
        hardhat_config_ts = self.project_path / "hardhat.config.ts"
        
        if not (hardhat_config.exists() or hardhat_config_ts.exists()):
            logger.warning("No hardhat.config.js found. Some features may not work.")
    
    def _check_foundry(self):
        """Check if Foundry is available."""
        foundry_toml = self.project_path / "foundry.toml"
        
        if not foundry_toml.exists():
            logger.warning("No foundry.toml found. Some features may not work.")
    
    # ─── Compilation ───────────────────────────────────────────────
    
    def compile_contract(
        self,
        contract_path: Optional[str] = None,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Compile smart contracts.
        
        Args:
            contract_path: Specific contract to compile (optional)
            optimize: Enable optimizer
            
        Returns:
            Compilation result with artifacts
        """
        logger.info(f"Compiling contracts with {self.framework}...")
        
        if self.framework == "hardhat":
            return self._compile_hardhat(contract_path, optimize)
        else:
            return self._compile_foundry(contract_path, optimize)
    
    def _compile_hardhat(
        self,
        contract_path: Optional[str],
        optimize: bool
    ) -> Dict[str, Any]:
        """Compile with Hardhat."""
        try:
            cmd = ["npx", "hardhat", "compile"]
            if contract_path:
                cmd.extend(["--contracts", contract_path])
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise CompilationError(f"Hardhat compilation failed: {result.stderr}")
            
            # Read artifacts
            artifacts = self._read_hardhat_artifacts()
            
            return {
                "success": True,
                "framework": "hardhat",
                "contracts": list(artifacts.keys()),
                "artifacts": artifacts,
                "output": result.stdout,
                "created": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            raise CompilationError("Compilation timed out")
        except Exception as e:
            raise CompilationError(f"Compilation error: {e}")
    
    def _compile_foundry(
        self,
        contract_path: Optional[str],
        optimize: bool
    ) -> Dict[str, Any]:
        """Compile with Foundry."""
        try:
            cmd = ["forge", "build"]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise CompilationError(f"Foundry compilation failed: {result.stderr}")
            
            # Read artifacts
            artifacts = self._read_foundry_artifacts()
            
            return {
                "success": True,
                "framework": "foundry",
                "contracts": list(artifacts.keys()),
                "artifacts": artifacts,
                "output": result.stdout,
                "created": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            raise CompilationError("Compilation timed out")
        except Exception as e:
            raise CompilationError(f"Compilation error: {e}")
    
    def _read_hardhat_artifacts(self) -> Dict[str, Any]:
        """Read Hardhat artifacts."""
        artifacts = {}
        artifacts_dir = self.project_path / "artifacts" / "contracts"
        
        if not artifacts_dir.exists():
            return artifacts
        
        for contract_file in artifacts_dir.glob("**/*.json"):
            if ".dbg.json" in str(contract_file):
                continue
            try:
                with open(contract_file) as f:
                    data = json.load(f)
                    contract_name = contract_file.stem
                    artifacts[contract_name] = {
                        "abi": data.get("abi", []),
                        "bytecode": data.get("bytecode", ""),
                        "path": str(contract_file)
                    }
            except Exception:
                continue
        
        return artifacts
    
    def _read_foundry_artifacts(self) -> Dict[str, Any]:
        """Read Foundry artifacts."""
        artifacts = {}
        out_dir = self.project_path / "out"
        
        if not out_dir.exists():
            return artifacts
        
        for contract_file in out_dir.glob("**/*.json"):
            if ".dbg.json" in str(contract_file):
                continue
            try:
                with open(contract_file) as f:
                    data = json.load(f)
                    contract_name = contract_file.stem
                    artifacts[contract_name] = {
                        "abi": data.get("abi", []),
                        "bytecode": data.get("bytecode", {}).get("object", ""),
                        "path": str(contract_file)
                    }
            except Exception:
                continue
        
        return artifacts
    
    # ─── Testing ────────────────────────────────────────────────────
    
    def run_contract_tests(
        self,
        test_path: Optional[str] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run contract tests.
        
        Args:
            test_path: Specific test file to run
            verbose: Enable verbose output
            
        Returns:
            Test results
        """
        logger.info(f"Running tests with {self.framework}...")
        
        if self.framework == "hardhat":
            return self._test_hardhat(test_path, verbose)
        else:
            return self._test_foundry(test_path, verbose)
    
    def _test_hardhat(
        self,
        test_path: Optional[str],
        verbose: bool
    ) -> Dict[str, Any]:
        """Run Hardhat tests."""
        try:
            cmd = ["npx", "hardhat", "test"]
            if test_path:
                cmd.append(test_path)
            if verbose:
                cmd.append("--verbose")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # Parse results
            passed = result.stdout.count("passed") or result.stdout.count("✓")
            failed = result.stdout.count("failed") or result.stdout.count("✗")
            
            return {
                "success": result.returncode == 0,
                "framework": "hardhat",
                "passed": passed,
                "failed": failed,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "created": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            raise TestError("Tests timed out")
        except Exception as e:
            raise TestError(f"Test error: {e}")
    
    def _test_foundry(
        self,
        test_path: Optional[str],
        verbose: bool
    ) -> Dict[str, Any]:
        """Run Foundry tests."""
        try:
            cmd = ["forge", "test"]
            if test_path:
                cmd.extend(["--match-path", test_path])
            if verbose:
                cmd.append("-vvvv")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # Parse results
            passed = result.stdout.count("[PASS]")
            failed = result.stdout.count("[FAIL]")
            
            return {
                "success": result.returncode == 0,
                "framework": "foundry",
                "passed": passed,
                "failed": failed,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "created": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            raise TestError("Tests timed out")
        except Exception as e:
            raise TestError(f"Test error: {e}")
    
    # ─── Deployment ──────────────────────────────────────────────────
    
    def deploy_contract(
        self,
        contract_name: str,
        network: str = "localhost",
        constructor_args: Optional[List] = None,
        simulate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Deploy a smart contract.
        
        Args:
            contract_name: Name of contract to deploy
            network: Network to deploy to
            constructor_args: Constructor arguments
            simulate_only: Only simulate, don't actually deploy
            
        Returns:
            Deployment result
        """
        if simulate_only:
            return self._simulate_deployment(contract_name, network, constructor_args)
        
        # Require HITL approval for mainnet
        if network in ["mainnet", "ethereum", "polygon", "arbitrum"]:
            return {
                "success": False,
                "error": "Mainnet deployment requires explicit HITL approval",
                "network": network,
                "contract": contract_name,
                "requires_approval": True
            }
        
        logger.info(f"Deploying {contract_name} to {network}...")
        
        if self.framework == "hardhat":
            return self._deploy_hardhat(contract_name, network, constructor_args)
        else:
            return self._deploy_foundry(contract_name, network, constructor_args)
    
    def _simulate_deployment(
        self,
        contract_name: str,
        network: str,
        constructor_args: Optional[List]
    ) -> Dict[str, Any]:
        """Simulate deployment without actually deploying."""
        return {
            "success": True,
            "simulated": True,
            "contract": contract_name,
            "network": network,
            "constructor_args": constructor_args or [],
            "gas_estimate": 1000000,  # Mock estimate
            "message": "Simulation complete. Ready for deployment.",
            "created": datetime.now().isoformat()
        }
    
    def _deploy_hardhat(
        self,
        contract_name: str,
        network: str,
        constructor_args: Optional[List]
    ) -> Dict[str, Any]:
        """Deploy with Hardhat."""
        try:
            # This would run a deployment script
            cmd = ["npx", "hardhat", "run", "scripts/deploy.js", "--network", network]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "framework": "hardhat",
                "contract": contract_name,
                "network": network,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise DeploymentError(f"Deployment error: {e}")
    
    def _deploy_foundry(
        self,
        contract_name: str,
        network: str,
        constructor_args: Optional[List]
    ) -> Dict[str, Any]:
        """Deploy with Foundry."""
        try:
            # This would use forge create
            cmd = ["forge", "create", contract_name, "--rpc-url", network]
            if constructor_args:
                cmd.extend(["--constructor-args"] + [str(a) for a in constructor_args])
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "framework": "foundry",
                "contract": contract_name,
                "network": network,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "created": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise DeploymentError(f"Deployment error: {e}")
    
    # ─── Analysis ────────────────────────────────────────────────────
    
    def analyze_compilation_error(
        self,
        error_output: str
    ) -> Dict[str, Any]:
        """
        Analyze compilation errors and suggest fixes.
        
        Args:
            error_output: Compilation error output
            
        Returns:
            Analysis with suggested fixes
        """
        errors = []
        warnings = []
        
        # Parse common Solidity errors
        if "undeclared identifier" in error_output.lower():
            errors.append({
                "type": "undeclared_identifier",
                "message": "Variable or function not declared",
                "suggestion": "Check spelling or import the identifier"
            })
        
        if "type error" in error_output.lower():
            errors.append({
                "type": "type_error",
                "message": "Type mismatch",
                "suggestion": "Check type compatibility"
            })
        
        if "stack too deep" in error_output.lower():
            errors.append({
                "type": "stack_too_deep",
                "message": "Too many local variables",
                "suggestion": "Reduce local variables or use structs"
            })
        
        if "warning" in error_output.lower():
            warnings.append({
                "type": "warning",
                "message": "Compiler warning detected"
            })
        
        return {
            "errors": errors,
            "warnings": warnings,
            "raw_output": error_output,
            "created": datetime.now().isoformat()
        }


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    contract = Web3Contract()
    
    if len(sys.argv) < 2:
        print("Usage: python web3_contract.py <command> [args]")
        print("\nCommands:")
        print("  compile [contract]  Compile contracts")
        print("  test [test_file]    Run tests")
        print("  deploy <contract>   Deploy contract")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "compile":
        result = contract.compile_contract(sys.argv[2] if len(sys.argv) > 2 else None)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == "test":
        result = contract.run_contract_tests(sys.argv[2] if len(sys.argv) > 2 else None)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == "deploy":
        contract_name = sys.argv[2]
        result = contract.deploy_contract(contract_name, simulate_only=True)
        print(json.dumps(result, indent=2, default=str))
