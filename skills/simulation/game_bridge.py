import json
import logging
import sys
import numpy as np

try:
    import gymnasium as gym
except ImportError:
    gym = None

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("game_bridge")

class GameBridge:
    def __init__(self):
        self.env = None
        self.env_name = None

    def _serialize(self, obj):
        """Recursively convert NumPy arrays and specialized types into pure Python types for JSON."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {str(k): self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize(i) for i in obj]
        return obj

    def initialize(self, env_name: str) -> dict:
        """Initializes a new gymnasium environment."""
        if gym is None:
            return {"error": "gymnasium is not installed. Run: pip install gymnasium"}

        try:
            if self.env:
                self.env.close()
            
            self.env_name = env_name
            self.env = gym.make(env_name)
            observation, info = self.env.reset()
            return {
                "status": "initialized",
                "environment": env_name,
                "observation": self._serialize(observation),
                "info": self._serialize(info)
            }
        except gym.error.Error as e:
            self.env = None
            return {"error": f"Gymnasium error: {str(e)}"}
        except Exception as e:
            self.env = None
            return {"error": f"Failed to initialize environment: {str(e)}"}

    def reset(self) -> dict:
        """Resets the current environment."""
        if not self.env:
            return {"error": "No environment initialized. Call initialize() first."}
        
        try:
            observation, info = self.env.reset()
            return {
                "status": "reset",
                "observation": self._serialize(observation),
                "info": self._serialize(info)
            }
        except Exception as e:
            return {"error": f"Failed to reset environment: {str(e)}"}

    def step(self, action) -> dict:
        """Takes a discrete or continuous action in the environment."""
        if not self.env:
            return {"error": "No environment initialized. Call initialize() first."}
        
        try:
            # Handle string conversions if necessary (some agents send strings instead of ints)
            if isinstance(action, str) and action.isdigit():
                action = int(action)
                
            observation, reward, terminated, truncated, info = self.env.step(action)
            
            return {
                "status": "stepped",
                "observation": self._serialize(observation),
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "info": self._serialize(info)
            }
        except Exception as e:
            return {"error": f"Failed to step environment: {str(e)}"}

    def close(self):
        if self.env:
            self.env.close()
            self.env = None

# Simple CLI exposed for the Agent to use locally
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command. Use: init, reset, step"}))
        sys.exit(1)

    cmd = sys.argv[1].lower()
    bridge = GameBridge()

    if cmd == "init":
        env_name = sys.argv[2] if len(sys.argv) > 2 else "CartPole-v1"
        print(json.dumps(bridge.initialize(env_name)))
    elif cmd == "reset":
        # In a real daemon, the bridge state would persist. For single-shot CLI execution,
        # we realistically just init and reset in one go, but this exposes the API design.
        print(json.dumps({"error": "Reset must be called within an active session process."}))
    elif cmd == "step":
        print(json.dumps({"error": "Step must be called within an active session process."}))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
