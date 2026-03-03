#!/usr/bin/env python3
"""test_terraform.py - Tests for Terraform runner."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.devops.terraform import TerraformRunner, AWSProvisioner


class TestTerraformRunnerMock(unittest.TestCase):
    """Test Terraform runner in mock mode."""
    
    def setUp(self):
        """Set up test runner."""
        self.work_dir = tempfile.mkdtemp()
        os.environ["TF_WORK_DIR"] = self.work_dir
        os.environ["AWS_ACCESS_KEY_ID"] = ""
        os.environ["AWS_SECRET_ACCESS_KEY"] = ""
        self.runner = TerraformRunner()
    
    def test_mock_mode(self):
        """Test that runner starts in mock mode."""
        self.assertFalse(self.runner._terraform_available)
    
    def test_init_mock(self):
        """Test init in mock mode."""
        result = self.runner.init()
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_plan_mock(self):
        """Test plan in mock mode."""
        result = self.runner.plan()
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_apply_mock(self):
        """Test apply in mock mode."""
        result = self.runner.apply()
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_destroy_mock(self):
        """Test destroy in mock mode."""
        result = self.runner.destroy()
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_output_mock(self):
        """Test output in mock mode."""
        result = self.runner.output()
        self.assertTrue(result["success"])
    
    def test_validate_mock(self):
        """Test validate in mock mode."""
        result = self.runner.validate()
        self.assertTrue(result["success"])


class TestAWSProvisionerMock(unittest.TestCase):
    """Test AWS provisioner in mock mode."""
    
    def setUp(self):
        """Set up test provisioner."""
        os.environ["AWS_ACCESS_KEY_ID"] = ""
        os.environ["AWS_SECRET_ACCESS_KEY"] = ""
        self.provisioner = AWSProvisioner()
    
    def test_mock_mode(self):
        """Test that provisioner starts in mock mode."""
        self.assertFalse(self.provisioner._aws_configured)
    
    def test_create_ec2_mock(self):
        """Test EC2 creation in mock mode."""
        result = self.provisioner.create_ec2("test-instance")
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_create_s3_mock(self):
        """Test S3 bucket creation in mock mode."""
        result = self.provisioner.create_s3_bucket("test-bucket")
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_create_rds_mock(self):
        """Test RDS creation in mock mode."""
        result = self.provisioner.create_rds("test-db")
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_region_config(self):
        """Test region configuration."""
        provisioner = AWSProvisioner(region="us-west-2")
        self.assertEqual(provisioner.region, "us-west-2")


class TestTerraformEnvironment(unittest.TestCase):
    """Test environment configuration."""
    
    def test_work_dir_config(self):
        """Test work directory configuration."""
        runner = TerraformRunner(work_dir="/tmp/tf")
        self.assertEqual(str(runner.work_dir), "/tmp/tf")
    
    def test_region_config(self):
        """Test region configuration."""
        os.environ["AWS_REGION"] = "eu-west-1"
        runner = TerraformRunner()
        self.assertEqual(runner.aws_region, "eu-west-1")


if __name__ == "__main__":
    unittest.main()
