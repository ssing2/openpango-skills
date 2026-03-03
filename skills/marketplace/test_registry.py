import unittest
import os
import sys
import sqlite3
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_client import SkillRegistry

class TestSkillRegistry(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the sqlite DB
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "test_registry.sqlite")
        self.registry = SkillRegistry(db_path=self.db_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_database_initialization(self):
        # Should seed with core skills
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM skills")
            count = cursor.fetchone()[0]
            self.assertGreaterEqual(count, 6)

    def test_publish_and_search(self):
        self.registry.publish(
            name="test-scraper",
            description="Extracts data from test sites",
            version="1.0.0",
            author="TestAgent",
            install_uri="github.com/testagent/scraper",
            capabilities=["web/testing", "data/extract"]
        )
        results = self.registry.search(query="scraper")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "test-scraper")
        self.assertIn("data/extract", results[0]["capabilities"])

    def test_search_core_skills(self):
        results = self.registry.search(query="Playwright")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "browser")

    def test_download_existing_skill(self):
        result = self.registry.download("browser")
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["skill"], "browser")
        self.assertEqual(result["install_uri"], "local")

    def test_download_missing_skill(self):
        result = self.registry.download("nonexistent-skill-xyz")
        self.assertEqual(result["status"], "not_found")

    def test_resolve_dependencies(self):
        # Publish a skill with a dependency
        self.registry.publish(
            name="advanced-scraper",
            description="Advanced scraping",
            version="1.0.0",
            author="AgentX",
            install_uri="github.com/agentx/advanced",
            dependencies=["browser"]
        )
        deps = self.registry.resolve_dependencies("advanced-scraper")
        # browser should come before advanced-scraper
        self.assertEqual(deps, ["browser", "advanced-scraper"])

    def test_publish_with_dependencies(self):
        self.registry.publish(
            name="captcha-solver",
            description="Solves captchas",
            version="1.0.0",
            author="AgentY",
            install_uri="github.com/agenty/captcha",
            dependencies=["browser", "memory"]
        )
        results = self.registry.search(query="captcha")
        self.assertEqual(len(results), 1)
        self.assertIn("browser", results[0]["dependencies"])
        self.assertIn("memory", results[0]["dependencies"])

    def test_transitive_dependencies(self):
        # A -> B -> C (browser is seeded)
        self.registry.publish(
            name="skill-b", description="Middle", version="1.0.0",
            author="t", install_uri="local", dependencies=["browser"]
        )
        self.registry.publish(
            name="skill-a", description="Top", version="1.0.0",
            author="t", install_uri="local", dependencies=["skill-b"]
        )
        deps = self.registry.resolve_dependencies("skill-a")
        # Should resolve: browser -> skill-b -> skill-a
        self.assertEqual(deps, ["browser", "skill-b", "skill-a"])

if __name__ == '__main__':
    unittest.main()

