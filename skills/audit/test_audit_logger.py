#!/usr/bin/env python3
"""test_audit_logger.py - Tests for audit logger."""

import os
import sys
import tempfile
import unittest
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.audit.audit_logger import AuditLogger


class TestAuditLogger(unittest.TestCase):
    """Test audit logger."""
    
    def setUp(self):
        """Set up test logger."""
        self.log_path = tempfile.mktemp(suffix=".db")
        self.logger = AuditLogger(log_path=self.log_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.log_path):
            os.unlink(self.log_path)
    
    def test_log_event(self):
        """Test logging an event."""
        record = self.logger.log(
            event_type="user_login",
            action="login",
            actor="alice",
            resource="system"
        )
        
        self.assertIn("id", record)
        self.assertIn("hash", record)
        self.assertEqual(record["event_type"], "user_login")
    
    def test_hash_chain(self):
        """Test hash chain integrity."""
        record1 = self.logger.log("test", "action1")
        record2 = self.logger.log("test", "action2")
        
        self.assertEqual(record2["prev_hash"], record1["hash"])
    
    def test_verify_empty(self):
        """Test verification of empty log."""
        result = self.logger.verify()
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_records"], 0)
    
    def test_verify_valid(self):
        """Test verification of valid log."""
        self.logger.log("test", "action1")
        self.logger.log("test", "action2")
        
        result = self.logger.verify()
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_records"], 2)
    
    def test_query_all(self):
        """Test querying all records."""
        self.logger.log("type1", "action1")
        self.logger.log("type2", "action2")
        
        records = self.logger.query()
        self.assertEqual(len(records), 2)
    
    def test_query_by_type(self):
        """Test querying by event type."""
        self.logger.log("type1", "action1")
        self.logger.log("type2", "action2")
        self.logger.log("type1", "action3")
        
        records = self.logger.query(event_type="type1")
        self.assertEqual(len(records), 2)
    
    def test_query_by_actor(self):
        """Test querying by actor."""
        self.logger.log("test", "action", actor="alice")
        self.logger.log("test", "action", actor="bob")
        self.logger.log("test", "action", actor="alice")
        
        records = self.logger.query(actor="alice")
        self.assertEqual(len(records), 2)
    
    def test_statistics(self):
        """Test statistics."""
        self.logger.log("type1", "action", actor="alice")
        self.logger.log("type1", "action", actor="bob")
        self.logger.log("type2", "action", actor="alice")
        
        stats = self.logger.get_statistics()
        
        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(len(stats["event_types"]), 2)
        self.assertEqual(len(stats["top_actors"]), 2)
    
    def test_export_json(self):
        """Test JSON export."""
        self.logger.log("test", "action")
        
        output_path = tempfile.mktemp(suffix=".json")
        result = self.logger.export_report(output_path, format="json")
        
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path) as f:
            report = json.load(f)
        
        self.assertIn("verification", report)
        os.unlink(output_path)
    
    def test_export_csv(self):
        """Test CSV export."""
        self.logger.log("test", "action")
        
        output_path = tempfile.mktemp(suffix=".csv")
        result = self.logger.export_report(output_path, format="csv")
        
        self.assertTrue(result["success"])
        self.assertTrue(os.path.exists(output_path))
        os.unlink(output_path)
    
    def test_details(self):
        """Test logging with details."""
        details = {"key": "value", "nested": {"a": 1}}
        record = self.logger.log("test", "action", details=details)
        
        self.assertEqual(record["details"], details)


if __name__ == "__main__":
    unittest.main()
