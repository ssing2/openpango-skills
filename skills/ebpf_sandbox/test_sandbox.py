#!/usr/bin/env python3
"""test_sandbox.py - Tests for eBPF sandbox."""

import os
import sys
import tempfile
import unittest
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.ebpf_sandbox.sandbox import EBFPSandbox, Enclave, EBPFError


class TestEnclave(unittest.TestCase):
    """Test Enclave class."""
    
    def test_enclave_creation(self):
        rootfs = tempfile.mkdtemp()
        enclave = Enclave("test-id", rootfs)
        
        self.assertEqual(enclave.id, "test-id")
        self.assertEqual(enclave.status, "created")
        self.assertEqual(len(enclave.allowed_syscalls), 0)
        
        shutil.rmtree(rootfs)
    
    def test_enclave_to_dict(self):
        rootfs = tempfile.mkdtemp()
        enclave = Enclave("test-id", rootfs)
        
        data = enclave.to_dict()
        
        self.assertEqual(data["id"], "test-id")
        self.assertEqual(data["status"], "created")
        
        shutil.rmtree(rootfs)


class TestEBFPSandbox(unittest.TestCase):
    """Test EBFPSandbox class."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sandbox = EBFPSandbox(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_enclave(self):
        enclave = self.sandbox.create_enclave()
        
        self.assertIsNotNone(enclave.id)
        self.assertIn(enclave.id, self.sandbox.enclaves)
        self.assertTrue(enclave.rootfs.exists())
    
    def test_create_enclave_with_id(self):
        enclave = self.sandbox.create_enclave(enclave_id="my-enclave")
        
        self.assertEqual(enclave.id, "my-enclave")
    
    def test_set_policy(self):
        enclave = self.sandbox.create_enclave()
        
        self.sandbox.set_policy(
            enclave.id,
            allowed_syscalls=["read", "write", "exit"],
            resource_limits={"cpu": 50, "memory": 100}
        )
        
        self.assertIn("read", enclave.allowed_syscalls)
        self.assertEqual(enclave.resource_limits["cpu"], 50)
    
    def test_execute_mock(self):
        enclave = self.sandbox.create_enclave()
        
        result = self.sandbox.execute(enclave.id, "ls -la")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_execute_invalid_enclave(self):
        with self.assertRaises(EBPFError):
            self.sandbox.execute("invalid", "ls")
    
    def test_destroy_enclave(self):
        enclave = self.sandbox.create_enclave()
        
        result = self.sandbox.destroy_enclave(enclave.id)
        
        self.assertTrue(result)
        self.assertNotIn(enclave.id, self.sandbox.enclaves)
    
    def test_list_enclaves(self):
        self.sandbox.create_enclave("enclave-1")
        self.sandbox.create_enclave("enclave-2")
        
        enclaves = self.sandbox.list_enclaves()
        
        self.assertEqual(len(enclaves), 2)
    
    def test_get_enclave(self):
        enclave = self.sandbox.create_enclave("test-enclave")
        
        found = self.sandbox.get_enclave("test-enclave")
        
        self.assertEqual(found.id, "test-enclave")
    
    def test_default_syscalls(self):
        self.assertGreater(len(EBFPSandbox.DEFAULT_ALLOWED_SYSCALLS), 0)
        self.assertIn("read", EBFPSandbox.DEFAULT_ALLOWED_SYSCALLS)
        self.assertIn("write", EBFPSandbox.DEFAULT_ALLOWED_SYSCALLS)


if __name__ == "__main__":
    unittest.main()
