import unittest
import os
import subprocess
import tempfile
import json
import time
from pathlib import Path

class TestOrchestrationRouter(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the workspace
        self.test_dir = tempfile.TemporaryDirectory()
        self.workspace_path = Path(self.test_dir.name)
        
        # Set environment variables for the subprocesses
        self.env = os.environ.copy()
        self.env["OPENCLAW_WORKSPACE"] = str(self.workspace_path)
        self.env["OPENCLAW_SYNC_EXECUTION"] = "1" # Force sync execution for tests
        self.env["OPENCLAW_ROUTER_DELAY"] = "0.1" # Fast processing delay
        
        self.router_script = Path(__file__).parent.parent / "orchestration" / "router.py"

    def tearDown(self):
        self.test_dir.cleanup()

    def run_router(self, *args):
        result = subprocess.run(
            ["python3", str(self.router_script), *args],
            env=self.env,
            capture_output=True,
            text=True
        )
        return result

    def test_full_lifecycle(self):
        # 1. Spawn a new session
        spawn_res = self.run_router("spawn", "coder")
        self.assertEqual(spawn_res.returncode, 0)
        session_id = spawn_res.stdout.strip()
        self.assertTrue(len(session_id) > 10)

        # 2. Check initial status
        status_res = self.run_router("status", session_id)
        self.assertEqual(status_res.returncode, 0)
        self.assertEqual(status_res.stdout.strip(), "idle")

        # 3. Append a task
        payload = json.dumps({"task": "Write a snake game"})
        append_res = self.run_router("append", session_id, payload)
        self.assertEqual(append_res.returncode, 0)

        # 4. In sync mode, by the time append returns, status should be idle again
        status_res = self.run_router("status", session_id)
        self.assertEqual(status_res.returncode, 0)
        self.assertEqual(status_res.stdout.strip(), "idle")

        # 5. Check output
        output_res = self.run_router("output", session_id)
        self.assertEqual(output_res.returncode, 0)
        outputs = json.loads(output_res.stdout)
        
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0]["payload"], payload)
        self.assertTrue("Successfully processed" in outputs[0]["result"])

if __name__ == "__main__":
    unittest.main()
