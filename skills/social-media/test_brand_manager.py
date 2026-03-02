import unittest
from brand_manager import BrandManager

class TestBrandManager(unittest.TestCase):
    def setUp(self):
        # The environment won't have the real tokens in CI, so this defaults to mock mode
        self.manager = BrandManager()
        
    def test_mock_mode_initialization(self):
        self.assertTrue(self.manager._mock_mode)

    def test_sentiment_analysis(self):
        sentiment = self.manager.analyze_sentiment("twitter")
        self.assertIn("Positive", sentiment)
        
    def test_generate_and_post_twitter(self):
        results = self.manager.generate_and_post(
            topic="New Release", 
            context="Added OAuth support",
            platforms=["twitter"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["platform"], "twitter")
        self.assertTrue(results[0]["mocked"])

    def test_generate_and_post_linkedin(self):
        results = self.manager.generate_and_post(
            topic="Enterprise Update", 
            context="Added Secure Enclaves",
            platforms=["linkedin"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["platform"], "linkedin")
        self.assertTrue(results[0]["mocked"])

    def test_invalid_platform(self):
        results = self.manager.generate_and_post(
            topic="Test", 
            context="Test",
            platforms=["myspace"]
        )
        # Should cleanly return an error dictionary, not crash
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "error")
        self.assertEqual(results[0]["platform"], "myspace")

if __name__ == '__main__':
    unittest.main()
