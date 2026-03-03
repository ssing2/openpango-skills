#!/usr/bin/env python3
"""test_hitl_manager.py - Tests for HITL manager."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.hitl.hitl_manager import HITLManager


class TestHITLManager(unittest.TestCase):
    """Test HITL manager."""
    
    def setUp(self):
        """Set up test manager."""
        self.db_path = tempfile.mktemp(suffix=".db")
        self.manager = HITLManager(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_request_approval(self):
        """Test creating approval request."""
        request = self.manager.request_approval(
            "send_email",
            {"to": "test@example.com", "subject": "Test"}
        )
        
        self.assertIn("id", request)
        self.assertEqual(request["action_type"], "send_email")
        self.assertEqual(request["status"], "pending")
    
    def test_get_pending(self):
        """Test getting pending requests."""
        self.manager.request_approval("test1", {})
        self.manager.request_approval("test2", {})
        
        pending = self.manager.get_pending()
        
        self.assertEqual(len(pending), 2)
    
    def test_approve(self):
        """Test approving request."""
        request = self.manager.request_approval("test", {})
        
        result = self.manager.process_approval(request["id"], True)
        
        self.assertEqual(result["status"], "approved")
    
    def test_reject(self):
        """Test rejecting request."""
        request = self.manager.request_approval("test", {})
        
        result = self.manager.process_approval(request["id"], False)
        
        self.assertEqual(result["status"], "rejected")
    
    def test_priority(self):
        """Test priority ordering."""
        self.manager.request_approval("low", {}, priority=0)
        self.manager.request_approval("high", {}, priority=10)
        
        pending = self.manager.get_pending()
        
        self.assertEqual(pending[0]["action_type"], "high")
    
    def test_history(self):
        """Test history."""
        r1 = self.manager.request_approval("test1", {})
        r2 = self.manager.request_approval("test2", {})
        
        self.manager.process_approval(r1["id"], True)
        
        history = self.manager.get_history()
        self.assertEqual(len(history), 2)
        
        approved = self.manager.get_history(status="approved")
        self.assertEqual(len(approved), 1)
    
    def test_statistics(self):
        """Test statistics."""
        r1 = self.manager.request_approval("test1", {})
        r2 = self.manager.request_approval("test2", {})
        
        self.manager.process_approval(r1["id"], True)
        self.manager.process_approval(r2["id"], False)
        
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats["pending"], 0)
        self.assertEqual(stats["approved"], 1)
        self.assertEqual(stats["rejected"], 1)
    
    def test_review_notes(self):
        """Test review notes."""
        request = self.manager.request_approval("test", {})
        
        result = self.manager.process_approval(
            request["id"],
            True,
            reviewed_by="alice",
            notes="Looks good"
        )
        
        self.assertEqual(result["reviewed_by"], "alice")
        self.assertEqual(result["review_notes"], "Looks good")


if __name__ == "__main__":
    unittest.main()
