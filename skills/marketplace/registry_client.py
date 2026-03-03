import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
import urllib.request
import urllib.parse
import urllib.error

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SkillRegistry")

class SkillRegistry:
    """
    Client for the OpenPango Decentralized Skill Registry.
    Enables agents to discover, search, and publish skills to the A2A Economy.
    """
    
    DEFAULT_REGISTRY_URL = "https://api.openpango.org/v1/registry"
    
    def __init__(self, db_path: str = None, registry_url: str = None):
        if db_path is None:
            # Default to tracking inside the workspace
            workspace = os.path.expanduser("~/.openclaw/workspace")
            os.makedirs(workspace, exist_ok=True)
            db_path = os.path.join(workspace, "registry_cache.sqlite")
            
        self.db_path = db_path
        self.registry_url = registry_url or self.DEFAULT_REGISTRY_URL
        self._init_db()
        
    def _init_db(self):
        """Initialize the local SQLite cache for skill discovery."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS skills (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT,
                    author TEXT,
                    install_uri TEXT NOT NULL,
                    capabilities TEXT,
                    dependencies TEXT DEFAULT '[]',
                    last_updated TIMESTAMP
                )
            ''')
            # Add dependencies column if missing (migration for existing DBs)
            try:
                conn.execute("SELECT dependencies FROM skills LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE skills ADD COLUMN dependencies TEXT DEFAULT '[]'")
            # Seed with core skills if empty
            cursor = conn.execute("SELECT count(*) FROM skills")
            if cursor.fetchone()[0] == 0:
                self._seed_core_skills(conn)
            conn.commit()

    def _seed_core_skills(self, conn):
        """Seed the db with known core skills to bootstrap discovery."""
        core_skills = [
            ("browser", "Playwright-based persistent daemon.", "1.0", "openpango", "local", "['web/browser', 'web/interaction']", "[]"),
            ("memory", "Event-sourced long-horizon task graph.", "1.0", "openpango", "local", "['core/memory', 'core/state']", "[]"),
            ("figma", "Figma Design-to-Code API.", "1.0", "moth-asa", "local", "['design/figma', 'code/css']", "[]"),
            ("orchestration", "Multi-agent task router.", "1.0", "openpango", "local", "['core/orchestration']", "[]"),
            ("marketplace", "Skill discovery and publishing.", "1.0", "openpango", "local", "['protocol/skill-discovery']", "[]"),
            ("self-improvement", "Captures learnings and proposes updates.", "1.1", "openpango", "local", "['core/self-improvement']", "[]"),
        ]
        conn.executemany(
            "INSERT INTO skills (id, name, description, version, author, install_uri, capabilities, dependencies, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(name, name, desc, ver, author, uri, caps, deps, datetime.now().isoformat()) for name, desc, ver, author, uri, caps, deps in core_skills]
        )

    def search(self, query: str = None, capability: str = None) -> List[Dict]:
        """
        Search for skills locally and (optionally) via the remote registry.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = "SELECT * FROM skills WHERE 1=1"
            params = []
            
            if query:
                sql += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
                
            if capability:
                sql += " AND capabilities LIKE ?"
                params.append(f"%{capability}%")
                
            cursor = conn.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            for r in results:
                try:
                    r['capabilities'] = json.loads(r['capabilities'].replace("'", "\""))
                except Exception:
                    r['capabilities'] = []
                try:
                    r['dependencies'] = json.loads(r.get('dependencies', '[]') or '[]')
                except Exception:
                    r['dependencies'] = []
                    
            return results

    def resolve_dependencies(self, skill_name: str) -> List[str]:
        """
        Resolve all transitive dependencies for a skill.
        Returns a flat, ordered list of skill names to install (dependencies first).
        """
        visited = set()
        order = []

        def _resolve(name):
            if name in visited:
                return
            visited.add(name)
            results = self.search(query=name)
            if results:
                deps = results[0].get('dependencies', [])
                for dep in deps:
                    _resolve(dep)
            order.append(name)

        _resolve(skill_name)
        return order

    def download(self, skill_name: str) -> Dict:
        """
        Look up a skill in the registry and return its install metadata.
        In a production system, this would download a zipped bundle.
        For now, it returns the install_uri and metadata needed by the CLI.
        """
        results = self.search(query=skill_name)
        exact = [r for r in results if r['name'] == skill_name or r['id'] == skill_name]
        
        if not exact:
            return {"status": "not_found", "skill": skill_name, "message": f"Skill '{skill_name}' not found in the marketplace registry."}
        
        skill = exact[0]
        deps = self.resolve_dependencies(skill_name)
        deps_needed = [d for d in deps if d != skill_name]
        
        return {
            "status": "found",
            "skill": skill['name'],
            "version": skill['version'],
            "author": skill['author'],
            "install_uri": skill['install_uri'],
            "dependencies": deps_needed,
            "message": f"Skill '{skill_name}' v{skill['version']} available from {skill['install_uri']}."
        }

    def publish(self, name: str, description: str, version: str, author: str, install_uri: str, capabilities: List[str] = None, dependencies: List[str] = None):
        """
        Publish a new skill to the local cache and the remote registry via API.
        """
        skill_id = f"{author}/{name}".lower().replace(" ", "-")
        now = datetime.now().isoformat()
        caps_json = json.dumps(capabilities or [])
        deps_json = json.dumps(dependencies or [])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO skills 
                (id, name, description, version, author, install_uri, capabilities, dependencies, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (skill_id, name, description, version, author, install_uri, caps_json, deps_json, now))
            conn.commit()
            
        logger.info(f"Successfully cached skill {skill_id} locally.")
        
        try:
            self._push_to_remote(skill_id, name, description, version, author, install_uri, capabilities)
            logger.info(f"Successfully published {skill_id} to global registry.")
        except Exception as e:
            logger.warning(f"Failed to push {skill_id} to remote registry: {e}. Available locally.")
            
        return {"id": skill_id, "status": "published"}

    def _push_to_remote(self, skill_id, name, description, version, author, install_uri, capabilities):
        """Mock network request to the central OpenPango registry."""
        payload = json.dumps({
            "id": skill_id, "name": name, "description": description,
            "version": version, "author": author, "install_uri": install_uri,
            "capabilities": capabilities
        }).encode('utf-8')
        
        # We mock the network call handling to demonstrate production intent
        req = urllib.request.Request(self.registry_url, data=payload, headers={'Content-Type': 'application/json'})
        try:
            # We expect this to fail in our local testing if the api isn't up
            urllib.request.urlopen(req, timeout=2)
        except urllib.error.URLError:
            raise Exception("Registry endpoint unreachable")

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenPango Skill Marketplace CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    search_parser = subparsers.add_parser("search", help="Search for a skill")
    search_parser.add_argument("query", type=str, help="Search term")
    
    download_parser = subparsers.add_parser("download", help="Look up a skill for download")
    download_parser.add_argument("skill_name", type=str, help="Skill name")
    
    deps_parser = subparsers.add_parser("deps", help="Resolve dependencies for a skill")
    deps_parser.add_argument("skill_name", type=str, help="Skill name")
    
    publish_parser = subparsers.add_parser("publish", help="Publish a skill")
    publish_parser.add_argument("--name", required=True)
    publish_parser.add_argument("--desc", required=True)
    publish_parser.add_argument("--uri", required=True)
    publish_parser.add_argument("--author", required=True)
    publish_parser.add_argument("--deps", nargs="*", default=[], help="Dependency skill names")
    
    args = parser.parse_args()
    registry = SkillRegistry()
    
    if args.command == "search":
        results = registry.search(query=args.query)
        print(json.dumps(results, indent=2))
    elif args.command == "download":
        result = registry.download(args.skill_name)
        print(json.dumps(result, indent=2))
    elif args.command == "deps":
        deps = registry.resolve_dependencies(args.skill_name)
        print(json.dumps({"skill": args.skill_name, "install_order": deps}, indent=2))
    elif args.command == "publish":
        res = registry.publish(args.name, args.desc, "1.0.0", args.author, args.uri, dependencies=args.deps)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()

