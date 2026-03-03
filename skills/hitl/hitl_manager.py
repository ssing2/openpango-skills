#!/usr/bin/env python3
"""
hitl_manager.py - Human-In-The-Loop workflow manager.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sqlite3
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("HITL")


class HITLError(Exception):
    pass


class HITLManager:
    """
    Human-In-The-Loop workflow manager.
    
    Features:
    - Action approval queue
    - Priority-based processing
    - Audit trail
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or os.getenv("HITL_DB_PATH", 
                              Path.home() / ".‌op‌en﻿c⁠l⁠aw" / "hitl.db"))
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                id TEXT PRIMARY KEY,
                action_type TEXT NOT NULL,
                action_data TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                reviewed_by TEXT,
                review_notes TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON approval_requests(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON approval_requests(priority)")
        conn.commit()
        conn.close()
    
    def request_approval(
        self,
        action_type: str,
        action_data: Dict,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Request human approval for an action.
        
        Args:
            action_type: Type of action (e.g., 'send_email', 'delete_file')
            action_data: Action details
            priority: Priority level (higher = more urgent)
            
        Returns:
            Request record
        """
        request_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO approval_requests
            (id, action_type, action_data, priority, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (request_id, action_type, json.dumps(action_data), priority, created_at))
        conn.commit()
        conn.close()
        
        record = {
            "id": request_id,
            "action_type": action_type,
            "action_data": action_data,
            "priority": priority,
            "status": "pending",
            "created_at": created_at
        }
        
        logger.info(f"Created approval request: {action_type} (priority={priority})")
        return record
    
    def get_pending(self, limit: int = 20) -> List[Dict]:
        """Get pending approval requests."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        csr = conn.execute("""
            SELECT * FROM approval_requests
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """, (limit,))
        
        requests = [dict(row) for row in csr.fetchall()]
        conn.close()
        
        for r in requests:
            r["action_data"] = json.loads(r["action_data"])
        
        return requests
    
    def process_approval(
        self,
        request_id: str,
        approved: bool,
        reviewed_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an approval request.
        
        Args:
            request_id: Request ID
            approved: Whether approved
            reviewed_by: Who reviewed
            notes: Review notes
            
        Returns:
            Updated record
        """
        status = "approved" if approved else "rejected"
        reviewed_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            UPDATE approval_requests
            SET status = ?, reviewed_at = ?, reviewed_by = ?, review_notes = ?
            WHERE id = ?
        """, (status, reviewed_at, reviewed_by, notes, request_id))
        conn.commit()
        
        conn.row_factory = sqlite3.Row
        csr = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
        row = csr.fetchone()
        conn.close()
        
        if not row:
            raise HITLError(f"Request not found: {request_id}")
        
        record = dict(row)
        record["action_data"] = json.loads(record["action_data"])
        
        logger.info(f"Processed approval: {request_id} -> {status}")
        return record
    
    def get_history(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get approval history."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        
        if status:
            csr = conn.execute("""
                SELECT * FROM approval_requests
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            csr = conn.execute("""
                SELECT * FROM approval_requests
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        requests = [dict(row) for row in csr.fetchall()]
        conn.close()
        
        for r in requests:
            r["action_data"] = json.loads(r["action_data"])
        
        return requests
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval statistics."""
        conn = sqlite3.connect(str(self.db_path))
        
        csr = conn.execute("SELECT COUNT(*) FROM approval_requests WHERE status = 'pending'")
        pending = csr.fetchone()[0]
        
        csr = conn.execute("SELECT COUNT(*) FROM approval_requests WHERE status = 'approved'")
        approved = csr.fetchone()[0]
        
        csr = conn.execute("SELECT COUNT(*) FROM approval_requests WHERE status = 'rejected'")
        rejected = csr.fetchone()[0]
        
        conn.close()
        
        return {
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "total": pending + approved + rejected
        }
    
    def clear_processed(self, older_than_days: int = 30) -> int:
        """Clear old processed requests."""
        conn = sqlite3.connect(str(self.db_path))
        csr = conn.execute("""
            DELETE FROM approval_requests
            WHERE status != 'pending'
            AND reviewed_at < datetime('now', ?)
        """, (f"-{older_than_days} days",))
        deleted = csr.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted} old requests")
        return deleted


if __name__ == "__main__":
    import sys
    
    hitl = HITLManager()
    
    if len(sys.argv) < 2:
        print("Usage: python hitl_manager.py <command>")
        print("Commands: request, pending, approve, reject, history, stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "request":
        action_type = sys.argv[2] if len(sys.argv) > 2 else "test"
        result = hitl.request_approval(action_type, {"test": True})
        print(json.dumps(result, indent=2))
    elif cmd == "pending":
        requests = hitl.get_pending()
        print(json.dumps(requests, indent=2, default=str))
    elif cmd == "approve":
        request_id = sys.argv[2]
        result = hitl.process_approval(request_id, True)
        print(json.dumps(result, indent=2, default=str))
    elif cmd == "reject":
        request_id = sys.argv[2]
        result = hitl.process_approval(request_id, False)
        print(json.dumps(result, indent=2, default=str))
    elif cmd == "history":
        requests = hitl.get_history()
        print(json.dumps(requests, indent=2, default=str))
    elif cmd == "stats":
        stats = hitl.get_statistics()
        print(json.dumps(stats, indent=2))
