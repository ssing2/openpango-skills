#!/usr/bin/env python3
"""
Unit tests for the self-improvement learnings_logger and promote tools.
Uses tempfile to avoid polluting the real ~/.openclaw directory.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent dir to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import learnings_logger
import promote


class TestLearningsLogger(unittest.TestCase):
    """Tests for learnings_logger.py"""

    def setUp(self):
        """Create a temp directory to act as ~/.openclaw/workspace."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "workspace"
        self.learnings = self.workspace / ".learnings"

        # Patch the module-level constants
        self.workspace_patch = patch.object(learnings_logger, "WORKSPACE_DIR", self.workspace)
        self.learnings_patch = patch.object(learnings_logger, "LEARNINGS_DIR", self.learnings)
        self.workspace_patch.start()
        self.learnings_patch.start()

    def tearDown(self):
        self.workspace_patch.stop()
        self.learnings_patch.stop()
        # Clean up temp dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_error_creates_file(self):
        """Test that log-error creates ERRORS.md and writes a structured entry."""
        result = learnings_logger.log_entry(
            log_type="log-error",
            summary="npm ERR! missing script: start",
            area="backend",
            priority="high",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("ERR-", result["id"])
        self.assertTrue((self.learnings / "ERRORS.md").exists())

        content = (self.learnings / "ERRORS.md").read_text()
        self.assertIn("npm ERR! missing script: start", content)
        self.assertIn("**Priority**: high", content)
        self.assertIn("**Area**: backend", content)

    def test_log_learning_creates_file(self):
        """Test that log-learning creates LEARNINGS.md with the correct category."""
        result = learnings_logger.log_entry(
            log_type="log-learning",
            summary="Always use --force for stale lockfiles",
            category="best_practice",
            area="infra",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("LRN-", result["id"])

        content = (self.learnings / "LEARNINGS.md").read_text()
        self.assertIn("best_practice", content)
        self.assertIn("Always use --force", content)

    def test_log_feature_request_creates_file(self):
        """Test that log-feature-request creates FEATURE_REQUESTS.md."""
        result = learnings_logger.log_entry(
            log_type="log-feature-request",
            summary="Add caching layer to API",
            area="backend",
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("FR-", result["id"])
        self.assertTrue((self.learnings / "FEATURE_REQUESTS.md").exists())

    def test_sequential_ids(self):
        """Test that sequential IDs are generated correctly for same-day entries."""
        r1 = learnings_logger.log_entry(log_type="log-error", summary="Error 1")
        r2 = learnings_logger.log_entry(log_type="log-error", summary="Error 2")
        r3 = learnings_logger.log_entry(log_type="log-error", summary="Error 3")

        # IDs should end with 001, 002, 003
        self.assertTrue(r1["id"].endswith("-001"))
        self.assertTrue(r2["id"].endswith("-002"))
        self.assertTrue(r3["id"].endswith("-003"))

    def test_details_and_action(self):
        """Test that details and action sections are included when provided."""
        result = learnings_logger.log_entry(
            log_type="log-learning",
            summary="Use retry logic for flaky APIs",
            details="The GitHub API occasionally returns 502 during peak hours.",
            action="Wrap all Octokit calls in a retry wrapper with exponential backoff.",
        )
        content = (self.learnings / "LEARNINGS.md").read_text()
        self.assertIn("### Details", content)
        self.assertIn("GitHub API occasionally returns 502", content)
        self.assertIn("### Suggested Action", content)
        self.assertIn("exponential backoff", content)


class TestPromote(unittest.TestCase):
    """Tests for promote.py"""

    def setUp(self):
        """Create a temp directory with a sample learning entry."""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "workspace"
        self.learnings = self.workspace / ".learnings"
        self.learnings.mkdir(parents=True)

        # Create a sample LEARNINGS.md with a test entry
        sample_content = """# Learnings

## [LRN-20260303-001] best_practice

**Logged**: 2026-03-03T10:00:00+00:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Always use --force for stale lockfiles

---
"""
        (self.learnings / "LEARNINGS.md").write_text(sample_content)

        # Patch the module-level constants for promote
        self.ws_patch = patch.object(promote, "WORKSPACE_DIR", self.workspace)
        self.lr_patch = patch.object(promote, "LEARNINGS_DIR", self.learnings)
        self.ws_patch.start()
        self.lr_patch.start()

    def tearDown(self):
        self.ws_patch.stop()
        self.lr_patch.stop()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_promote_creates_target_entry(self):
        """Test that promoting a learning appends to the target config file."""
        result = promote.promote_learning(
            learning_id="LRN-20260303-001",
            target="TOOLS.md",
            summary="Always use --force for stale lockfiles",
        )
        self.assertEqual(result["status"], "success")
        target_content = (self.workspace / "TOOLS.md").read_text()
        self.assertIn("[LRN-20260303-001]", target_content)
        self.assertIn("Always use --force", target_content)

    def test_promote_updates_status(self):
        """Test that the original learning entry status is updated to 'promoted'."""
        promote.promote_learning(
            learning_id="LRN-20260303-001",
            target="AGENTS.md",
            summary="Always use --force for stale lockfiles",
        )
        learnings_content = (self.learnings / "LEARNINGS.md").read_text()
        self.assertIn("**Status**: promoted", learnings_content)
        self.assertNotIn("**Status**: pending", learnings_content)

    def test_promote_nonexistent_id(self):
        """Test promoting a non-existent ID still creates the target entry gracefully."""
        result = promote.promote_learning(
            learning_id="LRN-99999999-999",
            target="SOUL.md",
            summary="Ghost learning",
        )
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["original_updated"])  # Should not find the entry


if __name__ == "__main__":
    unittest.main()
