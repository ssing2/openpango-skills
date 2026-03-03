"""
Immutable Audit Logging System
 cryptographic hash chain for tamper-proof audit trails
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio


class AuditLogger:
    """
    Immutable audit logger with cryptographic hash chaining.
    Each entry hashes the previous entry to create a tamper-proof chain.
    """
    
    def __init__(self, log_dir: str = "~/.openclaw/audit"):
        self.log_dir = Path(log_dir).expanduser()
        self.log_file = self.log_dir / "audit_chain.jsonl"
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Ensure log directory exists."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()
    
    def _compute_hash(self, entry: Dict[str, Any], prev_hash: str = "0" * 64) -> str:
        """Compute SHA-256 hash for an entry."""
        content = json.dumps({
            "prev_hash": prev_hash,
            "timestamp": entry.get("timestamp"),
            "action": entry.get("action"),
            "details": entry.get("details")
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_last_entry(self) -> Optional[Dict[str, Any]]:
        """Get the last entry in the chain."""
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            return None
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
        return None
    
    def log(self, action: str, details: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        """
        Log an action with details.
        
        Args:
            action: The action being logged (e.g., "tool_invocation", "file_modified")
            details: Dictionary of action details
            metadata: Optional metadata (user, session, etc.)
        
        Returns:
            The hash of the created entry
        """
        last_entry = self._get_last_entry()
        prev_hash = last_entry.get("hash", "0" * 64) if last_entry else "0" * 64
        
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "details": details,
            "metadata": metadata or {},
            "prev_hash": prev_hash
        }
        
        entry["hash"] = self._compute_hash(entry, prev_hash)
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return entry["hash"]
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit chain.
        
        Returns:
            Dictionary with verification results
        """
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            return {
                "valid": True,
                "entries": 0,
                "message": "Empty audit log"
            }
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return {"valid": True, "entries": 0, "message": "Empty audit log"}
        
        entries = [json.loads(line) for line in lines]
        errors = []
        
        for i, entry in enumerate(entries):
            expected_hash = entry.get("hash")
            prev_hash = entry.get("prev_hash")
            
            # Verify hash chain
            computed = self._compute_hash(entry, prev_hash)
            if computed != expected_hash:
                errors.append(f"Entry {i}: hash mismatch")
            
            # Verify previous hash links correctly
            if i > 0:
                if prev_hash != entries[i-1].get("hash"):
                    errors.append(f"Entry {i}: broken chain")
        
        return {
            "valid": len(errors) == 0,
            "entries": len(entries),
            "errors": errors,
            "first_hash": entries[0].get("hash") if entries else None,
            "last_hash": entries[-1].get("hash") if entries else None
        }
    
    def query(self, action: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Query audit logs with optional filtering."""
        if not self.log_file.exists():
            return []
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        entries = [json.loads(line) for line in lines]
        
        if action:
            entries = [e for e in entries if e.get("action") == action]
        
        return entries[-limit:]


# CLI Interface
def main():
    """CLI for audit logging operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Immutable Audit Logging System")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # log command
    log_parser = subparsers.add_parser("log", help="Log an action")
    log_parser.add_argument("action", help="Action to log")
    log_parser.add_argument("--details", default="{}", help="JSON details")
    
    # verify command
    subparsers.add_parser("verify", help="Verify audit chain integrity")
    
    # query command
    query_parser = subparsers.add_parser("query", help="Query audit logs")
    query_parser.add_argument("--action", help="Filter by action")
    query_parser.add_argument("--limit", type=int, default=100, help="Limit results")
    
    args = parser.parse_args()
    logger = AuditLogger()
    
    if args.command == "log":
        details = json.loads(args.details)
        hash_val = logger.log(args.action, details)
        print(f"Logged: {args.action}, hash: {hash_val[:16]}...")
    
    elif args.command == "verify":
        result = logger.verify_chain()
        if result["valid"]:
            print(f"✓ Chain valid ({result['entries']} entries)")
            print(f"  First: {result.get('first_hash', 'N/A')[:16]}...")
            print(f"  Last:  {result.get('last_hash', 'N/A')[:16]}...")
        else:
            print(f"✗ Chain INVALID:")
            for err in result["errors"]:
                print(f"  - {err}")
    
    elif args.command == "query":
        entries = logger.query(args.action, args.limit)
        for entry in entries:
            print(f"[{entry['timestamp']}] {entry['action']}: {entry['hash'][:16]}...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
