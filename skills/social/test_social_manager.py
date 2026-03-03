#!/usr/bin/env python3
"""test_social_manager.py - Tests for social manager."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.social.social_manager import SocialManager, SocialError


class TestTwitterClient(unittest.TestCase):
    """Test Twitter client."""
    
    def setUp(self):
        """Set up client."""
        os.environ["TWITTER_API_KEY"] = ""
        os.environ["TWITTER_API_SECRET"] = ""
        self.manager = SocialManager()
    
    def test_mock_mode(self):
        """Test mock mode."""
        self.assertFalse(self.manager.twitter._configured)
    
    def test_post_mock(self):
        """Test posting in mock mode."""
        result = self.manager.twitter.post("Test tweet")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_reply_mock(self):
        """Test reply in mock mode."""
        result = self.manager.twitter.reply("tweet_id", "Reply text")
        
        self.assertTrue(result["success"])
    
    def test_timeline_mock(self):
        """Test timeline in mock mode."""
        timeline = self.manager.twitter.get_timeline()
        
        self.assertIsInstance(timeline, list)


class TestLinkedInClient(unittest.TestCase):
    """Test LinkedIn client."""
    
    def setUp(self):
        """Set up client."""
        os.environ["LINKEDIN_ACCESS_TOKEN"] = ""
        self.manager = SocialManager()
    
    def test_mock_mode(self):
        """Test mock mode."""
        self.assertFalse(self.manager.linkedin._configured)
    
    def test_post_mock(self):
        """Test posting in mock mode."""
        result = self.manager.linkedin.post("Test post")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_share_article_mock(self):
        """Test sharing article in mock mode."""
        result = self.manager.linkedin.share_article(
            "https://example.com",
            "Test Article"
        )
        
        self.assertTrue(result["success"])


class TestFarcasterClient(unittest.TestCase):
    """Test Farcaster client."""
    
    def setUp(self):
        """Set up client."""
        os.environ["FARCASTER_MNEMONIC"] = ""
        self.manager = SocialManager()
    
    def test_mock_mode(self):
        """Test mock mode."""
        self.assertFalse(self.manager.farcaster._configured)
    
    def test_cast_mock(self):
        """Test casting in mock mode."""
        result = self.manager.farcaster.cast("Test cast")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["mock"])
    
    def test_reply_mock(self):
        """Test reply in mock mode."""
        result = self.manager.farcaster.reply("0xparent", "Reply")
        
        self.assertTrue(result["success"])
    
    def test_react_mock(self):
        """Test reaction in mock mode."""
        result = self.manager.farcaster.react("0xcast", "like")
        
        self.assertTrue(result["success"])


class TestSocialManager(unittest.TestCase):
    """Test social manager."""
    
    def setUp(self):
        """Set up manager."""
        self.manager = SocialManager()
    
    def test_post_to_platform(self):
        """Test posting to platform."""
        result = self.manager.post("twitter", "Test")
        
        self.assertTrue(result["success"])
    
    def test_post_to_invalid_platform(self):
        """Test posting to invalid platform."""
        with self.assertRaises(SocialError):
            self.manager.post("invalid", "Test")
    
    def test_post_all(self):
        """Test posting to all platforms."""
        results = self.manager.post_all("Test post")
        
        self.assertIn("twitter", results)
        self.assertIn("linkedin", results)
        self.assertIn("farcaster", results)
    
    def test_get_status(self):
        """Test getting status."""
        status = self.manager.get_status()
        
        self.assertIn("twitter", status)
        self.assertIn("linkedin", status)
        self.assertIn("farcaster", status)


if __name__ == "__main__":
    unittest.main()
