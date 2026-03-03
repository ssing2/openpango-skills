#!/usr/bin/env python3
"""test_stealth_engine.py - Tests for stealth engine."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.stealth.stealth_engine import StealthEngine


class TestStealthEngine(unittest.TestCase):
    """Test stealth engine."""
    
    def setUp(self):
        """Set up test engine."""
        self.engine = StealthEngine()
    
    def test_create_session(self):
        """Test creating session."""
        session_id = self.engine.create_session()
        
        self.assertIsNotNone(session_id)
        self.assertEqual(len(session_id), 16)
    
    def test_create_session_with_id(self):
        """Test creating session with custom ID."""
        session_id = self.engine.create_session("test-session")
        
        self.assertEqual(session_id, "test-session")
    
    def test_get_session(self):
        """Test getting session."""
        session_id = self.engine.create_session()
        session = self.engine.get_session(session_id)
        
        self.assertIn("fingerprint", session)
        self.assertIn("user_agent", session)
        self.assertIn("canvas_hash", session)
    
    def test_apply_randomization(self):
        """Test applying randomization."""
        session_id = self.engine.create_session()
        
        applied = self.engine.apply_randomization(session_id, ["canvas", "webgl"])
        
        self.assertIn("canvas", applied)
        self.assertIn("webgl", applied)
    
    def test_apply_randomization_invalid_session(self):
        """Test applying to invalid session."""
        with self.assertRaises(ValueError):
            self.engine.apply_randomization("invalid", ["canvas"])
    
    def test_rotate_user_agent(self):
        """Test rotating user agent."""
        session_id = self.engine.create_session()
        
        new_ua = self.engine.rotate_user_agent(session_id)
        
        self.assertIsNotNone(new_ua)
        self.assertIn("Mozilla", new_ua)
    
    def test_get_cdp_commands(self):
        """Test getting CDP commands."""
        session_id = self.engine.create_session()
        
        commands = self.engine.get_cdp_commands(session_id)
        
        self.assertIsInstance(commands, list)
        self.assertGreater(len(commands), 0)
        self.assertIn("method", commands[0])
    
    def test_close_session(self):
        """Test closing session."""
        session_id = self.engine.create_session()
        
        result = self.engine.close_session(session_id)
        
        self.assertTrue(result)
        with self.assertRaises(ValueError):
            self.engine.get_session(session_id)
    
    def test_fingerprint_generation(self):
        """Test fingerprint generation."""
        fp = self.engine._generate_fingerprint()
        
        self.assertIn("screen_width", fp)
        self.assertIn("screen_height", fp)
        self.assertIn("timezone", fp)
    
    def test_user_agents_loaded(self):
        """Test user agents are loaded."""
        self.assertGreater(len(self.engine._user_agents), 0)


if __name__ == "__main__":
    unittest.main()
