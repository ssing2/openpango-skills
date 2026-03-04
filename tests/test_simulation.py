import unittest
import os
import sys
import json
import numpy as np

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from skills.simulation.game_bridge import GameBridge


class TestSimulationBridge(unittest.TestCase):
    def setUp(self):
        self.bridge = GameBridge()
        
    def tearDown(self):
        self.bridge.close()

    def test_initialize_cartpole(self):
        """Test initializing a simple CartPole environment."""
        result = self.bridge.initialize("CartPole-v1")
        
        self.assertEqual(result.get("status"), "initialized")
        self.assertEqual(result.get("environment"), "CartPole-v1")
        
        # Ensure observation is successfully converted to list so JSON won't crash
        self.assertIsInstance(result.get("observation"), list)
        self.assertEqual(len(result.get("observation")), 4)  # CartPole observation size
        
        json.dumps(result) # Validate JSON serialization

    def test_reset_uninitialized(self):
        """Test reset without initialization."""
        result = self.bridge.reset()
        self.assertIn("error", result)

    def test_step_uninitialized(self):
        """Test step without initialization."""
        result = self.bridge.step(0)
        self.assertIn("error", result)

    def test_step_interaction(self):
        """Test taking an action and parsing the results."""
        self.bridge.initialize("CartPole-v1")
        
        # 0 = push cart left, 1 = push cart right
        action = 0
        result = self.bridge.step(action)
        
        self.assertEqual(result.get("status"), "stepped")
        self.assertIsInstance(result.get("observation"), list)
        self.assertIsInstance(result.get("reward"), float)
        self.assertIsInstance(result.get("terminated"), bool)
        self.assertIsInstance(result.get("truncated"), bool)
        self.assertIsInstance(result.get("info"), dict)
        
        json.dumps(result) # Validate JSON serialization

    def test_serialization(self):
        """Test internal NumPy serialization helper."""
        test_dict = {
            "arr": np.array([1, 2, 3], dtype=np.int32),
            "float": np.float64(42.5),
            "nested": {
                "arr2": np.array([[1.0, 2.0], [3.0, 4.0]])
            }
        }
        serialized = self.bridge._serialize(test_dict)
        
        self.assertIsInstance(serialized["arr"], list)
        self.assertIsInstance(serialized["float"], float)
        self.assertIsInstance(serialized["nested"]["arr2"], list)
        self.assertEqual(serialized["nested"]["arr2"][0], [1.0, 2.0])

if __name__ == '__main__':
    unittest.main()
