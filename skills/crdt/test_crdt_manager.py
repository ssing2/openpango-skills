#!/usr/bin/env python3
"""test_crdt_manager.py - Tests for CRDT manager."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.crdt.crdt_manager import (
    GCounter, PNCounter, LWWRegister, ORSet, CRDTManager
)


class TestGCounter(unittest.TestCase):
    """Test G-Counter."""
    
    def test_increment(self):
        counter = GCounter("node1")
        counter.increment()
        self.assertEqual(counter.value(), 1)
        counter.increment(5)
        self.assertEqual(counter.value(), 6)
    
    def test_merge(self):
        counter1 = GCounter("node1")
        counter2 = GCounter("node2")
        
        counter1.increment(5)
        counter2.increment(3)
        
        counter1.merge(counter2)
        self.assertEqual(counter1.value(), 8)


class TestPNCounter(unittest.TestCase):
    """Test PN-Counter."""
    
    def test_increment_decrement(self):
        counter = PNCounter("node1")
        counter.increment(5)
        counter.decrement(2)
        self.assertEqual(counter.value(), 3)
    
    def test_merge(self):
        counter1 = PNCounter("node1")
        counter2 = PNCounter("node2")
        
        counter1.increment(10)
        counter2.decrement(3)
        
        counter1.merge(counter2)
        self.assertEqual(counter1.value(), 7)


class TestLWWRegister(unittest.TestCase):
    """Test LWW-Register."""
    
    def test_set_get(self):
        reg = LWWRegister("node1")
        reg.set("value1")
        self.assertEqual(reg.get(), "value1")
    
    def test_merge_newer(self):
        reg1 = LWWRegister("node1")
        reg2 = LWWRegister("node2")
        
        reg1.set("old")
        import time
        time.sleep(0.001)
        reg2.set("new")
        
        reg1.merge(reg2)
        self.assertEqual(reg1.get(), "new")


class TestORSet(unittest.TestCase):
    """Test OR-Set."""
    
    def test_add_remove(self):
        s = ORSet("node1")
        s.add("a")
        s.add("b")
        self.assertTrue(s.contains("a"))
        self.assertTrue(s.contains("b"))
        
        s.remove("a")
        self.assertFalse(s.contains("a"))
        self.assertTrue(s.contains("b"))
    
    def test_merge(self):
        s1 = ORSet("node1")
        s2 = ORSet("node2")
        
        s1.add("a")
        s1.add("b")
        s2.add("c")
        
        s1.merge(s2)
        self.assertTrue(s1.contains("c"))


class TestCRDTManager(unittest.TestCase):
    """Test CRDT Manager."""
    
    def setUp(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.manager = CRDTManager("node1", self.db_path)
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_set_get(self):
        ts = self.manager.set("key1", "value1")
        self.assertIsNotNone(ts)
        self.assertEqual(self.manager.get("key1"), "value1")
    
    def test_counter(self):
        self.manager.increment("counter1", 5)
        self.manager.decrement("counter1", 2)
        self.assertEqual(self.manager.increment("counter1", 0), 3)
    
    def test_set_operations(self):
        self.manager.add_to_set("set1", "a")
        self.manager.add_to_set("set1", "b")
        
        elements = self.manager.get_set("set1")
        self.assertIn("a", elements)
        self.assertIn("b", elements)
        
        self.manager.remove_from_set("set1", "a")
        elements = self.manager.get_set("set1")
        self.assertNotIn("a", elements)
    
    def test_export_merge(self):
        manager1 = CRDTManager("node1", tempfile.mktemp(suffix=".db"))
        manager2 = CRDTManager("node2", tempfile.mktemp(suffix=".db"))
        
        manager1.set("key1", "value1")
        manager1.increment("counter1", 5)
        manager1.add_to_set("set1", "a")
        
        data = manager1.export()
        manager2.merge(data)
        
        self.assertEqual(manager2.get("key1"), "value1")
        self.assertEqual(manager2.increment("counter1", 0), 5)
        self.assertIn("a", manager2.get_set("set1"))


if __name__ == "__main__":
    unittest.main()
