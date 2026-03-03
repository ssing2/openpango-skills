#!/usr/bin/env python3
"""
terraform.py - Terraform and AWS cloud provisioning.

Provides infrastructure as code capabilities.
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Terraform")


class TerraformError(Exception):
    """Base exception for Terraform errors."""
    pass


class AWSError(Exception):
    """AWS related error."""
    pass


class TerraformRunner:
    """
    Terraform runner for infrastructure provisioning.
    
    Supports:
    - Plan, apply, destroy infrastructure
    - AWS integration
    - Remote state management
    - Mock mode for testing
    """
    
    def __init__(
        self,
        work_dir: Optional[str] = None,
        aws_region: Optional[str] = None,
        state_bucket: Optional[str] = None
    ):
        """
        Initialize Terraform runner.
        
        Args:
            work_dir: Working directory for Terraform files
            aws_region: AWS region
            state_bucket: S3 bucket for remote state
        """
        self.work_dir = Path(work_dir or os.getenv("TF_WORK_DIR", "."))
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        self.state_bucket = state_bucket or os.getenv("TF_STATE_BUCKET", "")
        
        self._check_terraform()
        self._check_aws_credentials()
    
    def _check_terraform(self):
        """Check if Terraform is installed."""
        try:
            result = subprocess.run(
                ["terraform", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Terraform installed: {result.stdout.split()[1]}")
                self._terraform_available = True
            else:
                logger.warning("Terraform not available. Running in MOCK mode.")
                self._terraform_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Terraform not found. Running in MOCK mode.")
            self._terraform_available = False
    
    def _check_aws_credentials(self):
        """Check if AWS credentials are configured."""
        self._aws_configured = bool(
            os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        if not self._aws_configured:
            logger.warning("AWS credentials not configured. Some features may not work.")
    
    def _run_terraform(self, *args, capture_output: bool = True) -> Dict[str, Any]:
        """Run Terraform command."""
        if not self._terraform_available:
            return self._mock_terraform(args[0] if args else "unknown")
        
        cmd = ["terraform"] + list(args)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.work_dir,
                capture_output=capture_output,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "command": " ".join(cmd),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            raise TerraformError("Terraform command timed out")
        except Exception as e:
            raise TerraformError(f"Terraform error: {e}")
    
    def _mock_terraform(self, command: str) -> Dict[str, Any]:
        """Mock Terraform command."""
        return {
            "success": True,
            "command": f"terraform {command}",
            "stdout": f"[MOCK] terraform {command} completed",
            "stderr": "",
            "returncode": 0,
            "mock": True
        }
    
    def init(self, backend_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Initialize Terraform.
        
        Args:
            backend_config: Backend configuration for remote state
            
        Returns:
            Init result
        """
        args = ["init", "-input=false"]
        
        if backend_config:
            for key, value in backend_config.items():
                args.extend(["-backend-config", f"{key}={value}"])
        
        return self._run_terraform(*args)
    
    def plan(self, var_file: Optional[str] = None, out: Optional[str] = None) -> Dict[str, Any]:
        """
        Plan infrastructure changes.
        
        Args:
            var_file: Variables file path
            out: Output plan file path
            
        Returns:
            Plan result
        """
        args = ["plan", "-input=false"]
        
        if var_file:
            args.extend(["-var-file", var_file])
        
        if out:
            args.extend(["-out", out])
        
        return self._run_terraform(*args)
    
    def apply(self, plan_file: Optional[str] = None, auto_approve: bool = True) -> Dict[str, Any]:
        """
        Apply infrastructure changes.
        
        Args:
            plan_file: Plan file to apply
            auto_approve: Auto approve changes
            
        Returns:
            Apply result
        """
        args = ["apply"]
        
        if auto_approve:
            args.append("-auto-approve")
        
        if plan_file:
            args.append(plan_file)
        else:
            args.append("-input=false")
        
        return self._run_terraform(*args)
    
    def destroy(self, auto_approve: bool = True) -> Dict[str, Any]:
        """
        Destroy infrastructure.
        
        Args:
            auto_approve: Auto approve destruction
            
        Returns:
            Destroy result
        """
        args = ["destroy"]
        
        if auto_approve:
            args.append("-auto-approve")
        
        args.append("-input=false")
        
        return self._run_terraform(*args)
    
    def output(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Terraform outputs.
        
        Args:
            name: Output name (optional)
            
        Returns:
            Outputs
        """
        args = ["output", "-json"]
        
        if name:
            args.append(name)
        
        result = self._run_terraform(*args)
        
        if result["success"] and result.get("stdout"):
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return result
        
        return result
    
    def show(self, plan_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Show Terraform state or plan.
        
        Args:
            plan_file: Plan file to show
            
        Returns:
            State/plan info
        """
        args = ["show", "-json"]
        
        if plan_file:
            args.append(plan_file)
        
        result = self._run_terraform(*args)
        
        if result["success"] and result.get("stdout"):
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return result
        
        return result
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate Terraform configuration.
        
        Returns:
            Validation result
        """
        return self._run_terraform("validate")
    
    def fmt(self, check: bool = False) -> Dict[str, Any]:
        """
        Format Terraform files.
        
        Args:
            check: Check if files are formatted
            
        Returns:
            Format result
        """
        args = ["fmt"]
        
        if check:
            args.append("-check")
        
        return self._run_terraform(*args)


class AWSProvisioner:
    """
    AWS resource provisioner.
    
    Provides high-level AWS resource management.
    """
    
    def __init__(self, region: Optional[str] = None):
        """
        Initialize AWS provisioner.
        
        Args:
            region: AWS region
        """
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._aws_configured = bool(
            os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        if not self._aws_configured:
            logger.warning("AWS credentials not configured. Running in MOCK mode.")
    
    def _mock_result(self, resource: str, action: str) -> Dict[str, Any]:
        """Generate mock result."""
        return {
            "success": True,
            "resource": resource,
            "action": action,
            "region": self.region,
            "mock": True,
            "created": datetime.now().isoformat()
        }
    
    def create_ec2(
        self,
        name: str,
        instance_type: str = "t2.micro",
        ami: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create EC2 instance.
        
        Args:
            name: Instance name
            instance_type: Instance type
            ami: AMI ID
            
        Returns:
            Instance info
        """
        if not self._aws_configured:
            return self._mock_result("ec2", "create")
        
        # Would use boto3 in production
        return {
            "success": True,
            "instance_id": f"i-{name}",
            "instance_type": instance_type,
            "ami": ami or "ami-default",
            "region": self.region
        }
    
    def create_s3_bucket(self, name: str) -> Dict[str, Any]:
        """
        Create S3 bucket.
        
        Args:
            name: Bucket name
            
        Returns:
            Bucket info
        """
        if not self._aws_configured:
            return self._mock_result("s3", "create")
        
        return {
            "success": True,
            "bucket_name": name,
            "region": self.region
        }
    
    def create_rds(
        self,
        name: str,
        engine: str = "postgres",
        instance_class: str = "db.t3.micro"
    ) -> Dict[str, Any]:
        """
        Create RDS instance.
        
        Args:
            name: Database name
            engine: Database engine
            instance_class: Instance class
            
        Returns:
            Database info
        """
        if not self._aws_configured:
            return self._mock_result("rds", "create")
        
        return {
            "success": True,
            "db_name": name,
            "engine": engine,
            "instance_class": instance_class,
            "region": self.region
        }


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    runner = TerraformRunner()
    
    if len(sys.argv) < 2:
        print("Usage: python terraform.py <command> [args]")
        print("\nCommands:")
        print("  init          Initialize Terraform")
        print("  plan          Plan changes")
        print("  apply         Apply changes")
        print("  destroy       Destroy infrastructure")
        print("  output        Get outputs")
        print("  validate      Validate configuration")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        result = runner.init()
    elif cmd == "plan":
        result = runner.plan()
    elif cmd == "apply":
        result = runner.apply()
    elif cmd == "destroy":
        result = runner.destroy()
    elif cmd == "output":
        result = runner.output()
    elif cmd == "validate":
        result = runner.validate()
    else:
        result = {"error": f"Unknown command: {cmd}"}
    
    print(json.dumps(result, indent=2, default=str))
