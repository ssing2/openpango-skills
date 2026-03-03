#!/usr/bin/env python3
"""
audit_logger.py - Immutable audit logging for enterprise compliance.
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sqlite3
import hmac

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("Audit")


class AuditError(Exception):
    pass


class AuditLogger:
    def __init__(self, log_path=None, sign_key=None, verify_key=None):
        self.log_path = Path(log_path or os.getenv("AUDIT_LOG_PATH", 
                              Path.home() / ".openclaw" / "audit.db"))
        self.sign_key = sign_key or os.getenv("AUDIT_SIGN_KEY", "").encode()
        self.verify_key = verify_key or os.getenv("AUDIT_VERIFY_KEY", "").encode()
        self._init_db()
    
    def _init_db(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.log_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                prev_hash TEXT,
                hash TEXT NOT NULL,
                signature TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_log(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_actor ON audit_log(actor)")
        conn.commit()
        conn.close()
    
    def _compute_hash(self, record):
        data = json.dumps(record, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _sign(self, data):
        if not self.sign_key:
            return ""
        return hmac.new(self.sign_key, data.encode(), hashlib.sha256).hexdigest()
    
    def _verify_signature(self, data, signature):
        if not self.verify_key or not signature:
            return True
        expected = hmac.new(self.verify_key, data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    
    def log(self, event_type, action, actor=None, resource=None, details=None):
        timestamp = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(str(self.log_path))
        csr = conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
        row = csr.fetchone()
        prev_hash = row[0] if row else "0" * 64
        
        record = {
            "timestamp": timestamp,
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "resource": resource,
            "details": details,
            "prev_hash": prev_hash
        }
        
        record_hash = self._compute_hash(record)
        record["hash"] = record_hash
        signature = self._sign(record_hash)
        
        conn.execute("""
            INSERT INTO audit_log 
            (timestamp, event_type, actor, action, resource, details, prev_hash, hash, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, event_type, actor, action, resource,
            json.dumps(details) if details else None,
            prev_hash, record_hash, signature
        ))
        conn.commit()
        
        csr = conn.execute("SELECT last_insert_rowid()")
        record_id = csr.fetchone()[0]
        conn.close()
        
        record["id"] = record_id
        logger.info(f"Logged audit event: {event_type} by {actor or 'system'}")
        return record
    
    def verify(self):
        conn = sqlite3.connect(str(self.log_path))
        conn.row_factory = sqlite3.Row
        csr = conn.execute("SELECT * FROM audit_log ORDER BY id")
        records = [dict(row) for row in csr.fetchall()]
        conn.close()
        
        errors = []
        prev_hash = "0" * 64
        
        for i, record in enumerate(records):
            if record["prev_hash"] != prev_hash:
                errors.append({
                    "record_id": record["id"],
                    "error": "Hash chain broken"
                })
            
            rec_data = {
                "timestamp": record["timestamp"],
                "event_type": record["event_type"],
                "actor": record["actor"],
                "action": record["action"],
                "resource": record["resource"],
                "details": json.loads(record["details"]) if record["details"] else None,
                "prev_hash": record["prev_hash"]
            }
            
            computed_hash = self._compute_hash(rec_data)
            if computed_hash != record["hash"]:
                errors.append({
                    "record_id": record["id"],
                    "error": "Hash mismatch"
                })
            
            if record["signature"] and not self._verify_signature(record["hash"], record["signature"]):
                errors.append({
                    "record_id": record["id"],
                    "error": "Signature verification failed"
                })
            
            prev_hash = record["hash"]
        
        return {
            "valid": len(errors) == 0,
            "total_records": len(records),
            "errors": errors,
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def query(self, event_type=None, actor=None, start_time=None, end_time=None, limit=100):
        conn = sqlite3.connect(str(self.log_path))
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if actor:
            query += " AND actor = ?"
            params.append(actor)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        csr = conn.execute(query, params)
        records = [dict(row) for row in csr.fetchall()]
        conn.close()
        
        return records
    
    def export_report(self, output_path, format="json", compliance="SOC2"):
        conn = sqlite3.connect(str(self.log_path))
        conn.row_factory = sqlite3.Row
        csr = conn.execute("SELECT * FROM audit_log ORDER BY timestamp")
        records = [dict(row) for row in csr.fetchall()]
        conn.close()
        
        report = {
            "report_type": f"{compliance} Compliance Report",
            "generated_at": datetime.utcnow().isoformat(),
            "total_records": len(records),
            "compliance_standard": compliance,
            "verification": self.verify(),
            "records": records
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        elif format == "csv":
            import csv
            with open(output_path, "w", newline="") as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
        
        return {
            "success": True,
            "output_path": output_path,
            "format": format,
            "records_exported": len(records)
        }
    
    def get_statistics(self):
        conn = sqlite3.connect(str(self.log_path))
        
        csr = conn.execute("SELECT COUNT(*) FROM audit_log")
        total = csr.fetchone()[0]
        
        csr = conn.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM audit_log 
            GROUP BY event_type 
            ORDER BY count DESC
        """)
        event_types = [{"type": row[0], "count": row[1]} for row in csr.fetchall()]
        
        csr = conn.execute("""
            SELECT actor, COUNT(*) as count 
            FROM audit_log 
            WHERE actor IS NOT NULL
            GROUP BY actor 
            ORDER BY count DESC 
            LIMIT 10
        """)
        actors = [{"actor": row[0], "count": row[1]} for row in csr.fetchall()]
        
        csr = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM audit_log")
        time_range = csr.fetchone()
        
        conn.close()
        
        return {
            "total_records": total,
            "event_types": event_types,
            "top_actors": actors,
            "time_range": {
                "start": time_range[0],
                "end": time_range[1]
            }
        }


if __name__ == "__main__":
    import sys
    
    audit = AuditLogger()
    
    if len(sys.argv) < 2:
        print("Usage: python audit_logger.py <command>")
        print("Commands: log, verify, query, stats, export")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "log":
        event_type = sys.argv[2] if len(sys.argv) > 2 else "test"
        action = sys.argv[3] if len(sys.argv) > 3 else "action"
        result = audit.log(event_type, action, actor="cli")
        print(json.dumps(result, indent=2, default=str))
    elif cmd == "verify":
        result = audit.verify()
        print(json.dumps(result, indent=2))
    elif cmd == "query":
        records = audit.query()
        print(json.dumps(records, indent=2, default=str))
    elif cmd == "stats":
        stats = audit.get_statistics()
        print(json.dumps(stats, indent=2))
    elif cmd == "export":
        path = sys.argv[2] if len(sys.argv) > 2 else "report.json"
        result = audit.export_report(path)
        print(json.dumps(result, indent=2))
