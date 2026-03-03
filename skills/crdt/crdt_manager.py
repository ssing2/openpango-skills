#!/usr/bin/env python3
"""
crdt_manager.py - Distributed CRDT Memory Graph with Hybrid Logical Clocks.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from pathlib import Path
import sqlite3
import hashlib
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("CRDT")


class HybridLogicalClock:
    """Hybrid Logical Clock for distributed ordering."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.counter = 0
        self.timestamp = int(time.time() * 1000)
        self._lock = threading.Lock()
    
    def tick(self) -> Tuple[int, int, str]:
        """Increment clock and return timestamp."""
        with self._lock:
            now = int(time.time() * 1000)
            self.timestamp = max(self.timestamp, now)
            self.counter += 1
            return (self.timestamp, self.counter, self.node_id)
    
    def update(self, other_ts: Tuple[int, int, str]) -> Tuple[int, int, str]:
        """Update clock with remote timestamp."""
        with self._lock:
            now = int(time.time() * 1000)
            other_time, other_counter, other_node = other_ts
            
            self.timestamp = max(self.timestamp, other_time, now)
            if self.timestamp == other_time:
                self.counter = max(self.counter, other_counter) + 1
            else:
                self.counter += 1
            
            return (self.timestamp, self.counter, self.node_id)
    
    def now(self) -> Tuple[int, int, str]:
        """Get current timestamp."""
        with self._lock:
            return (self.timestamp, self.counter, self.node_id)


class GCounter:
    """Grow-only Counter CRDT."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.counts: Dict[str, int] = {node_id: 0}
    
    def increment(self, delta: int = 1):
        """Increment counter."""
        self.counts[self.node_id] = self.counts.get(self.node_id, 0) + delta
    
    def value(self) -> int:
        """Get total value."""
        return sum(self.counts.values())
    
    def merge(self, other: 'GCounter'):
        """Merge with another counter."""
        for node, count in other.counts.items():
            self.counts[node] = max(self.counts.get(node, 0), count)
    
    def to_dict(self) -> Dict:
        return {"counts": self.counts, "node_id": self.node_id}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GCounter':
        counter = cls(data["node_id"])
        counter.counts = data["counts"]
        return counter


class PNCounter:
    """Positive-Negative Counter CRDT."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.p = GCounter(node_id)
        self.n = GCounter(node_id)
    
    def increment(self, delta: int = 1):
        self.p.increment(delta)
    
    def decrement(self, delta: int = 1):
        self.n.increment(delta)
    
    def value(self) -> int:
        return self.p.value() - self.n.value()
    
    def merge(self, other: 'PNCounter'):
        self.p.merge(other.p)
        self.n.merge(other.n)
    
    def to_dict(self) -> Dict:
        return {"p": self.p.to_dict(), "n": self.n.to_dict(), "node_id": self.node_id}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PNCounter':
        counter = cls(data["node_id"])
        counter.p = GCounter.from_dict(data["p"])
        counter.n = GCounter.from_dict(data["n"])
        return counter


class LWWRegister:
    """Last-Writer-Wins Register CRDT."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.hlc = HybridLogicalClock(node_id)
        self.value: Any = None
        self.timestamp: Tuple[int, int, str] = (0, 0, node_id)
    
    def set(self, value: Any):
        """Set value with timestamp."""
        self.value = value
        self.timestamp = self.hlc.tick()
    
    def get(self) -> Any:
        return self.value
    
    def merge(self, other: 'LWWRegister'):
        """Merge with another register."""
        other_ts = other.timestamp
        other_time, other_counter, other_node = other_ts
        self_time, self_counter, _ = self.timestamp
        
        if (other_time, other_counter, other_node) > (self_time, self_counter, self.node_id):
            self.value = other.value
            self.timestamp = other_ts
            self.hlc.update(other_ts)
    
    def to_dict(self) -> Dict:
        return {
            "value": self.value,
            "timestamp": list(self.timestamp),
            "node_id": self.node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LWWRegister':
        reg = cls(data["node_id"])
        reg.value = data["value"]
        reg.timestamp = tuple(data["timestamp"])
        return reg


class ORSet:
    """Observed-Remove Set CRDT."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.hlc = HybridLogicalClock(node_id)
        self.elements: Dict[str, Set[Tuple[int, int, str]]] = {}
        self.tombstones: Dict[str, Set[Tuple[int, int, str]]] = {}
    
    def add(self, element: str):
        """Add element."""
        ts = self.hlc.tick()
        if element not in self.elements:
            self.elements[element] = set()
        self.elements[element].add(ts)
    
    def remove(self, element: str):
        """Remove element."""
        if element in self.elements:
            if element not in self.tombstones:
                self.tombstones[element] = set()
            self.tombstones[element].update(self.elements[element])
            del self.elements[element]
    
    def contains(self, element: str) -> bool:
        return element in self.elements
    
    def get_all(self) -> Set[str]:
        return set(self.elements.keys())
    
    def merge(self, other: 'ORSet'):
        """Merge with another set."""
        # Merge elements
        for elem, tags in other.elements.items():
            if elem not in self.elements:
                self.elements[elem] = set()
            self.elements[elem].update(tags - self.tombstones.get(elem, set()))
        
        # Merge tombstones
        for elem, tags in other.tombstones.items():
            if elem not in self.tombstones:
                self.tombstones[elem] = set()
            self.tombstones[elem].update(tags)
            if elem in self.elements:
                self.elements[elem] -= tags
                if not self.elements[elem]:
                    del self.elements[elem]
        
        # Update clock
        for elem in other.elements:
            for ts in other.elements[elem]:
                self.hlc.update(ts)
    
    def to_dict(self) -> Dict:
        return {
            "elements": {k: [list(t) for t in v] for k, v in self.elements.items()},
            "tombstones": {k: [list(t) for t in v] for k, v in self.tombstones.items()},
            "node_id": self.node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ORSet':
        s = cls(data["node_id"])
        s.elements = {k: {tuple(t) for t in v} for k, v in data["elements"].items()}
        s.tombstones = {k: {tuple(t) for t in v} for k, v in data.get("tombstones", {}).items()}
        return s


class CRDTManager:
    """
    CRDT Memory Graph Manager.
    
    Provides distributed memory storage with CRDT data types.
    """
    
    def __init__(self, node_id: str, db_path: Optional[str] = None):
        self.node_id = node_id
        self.hlc = HybridLogicalClock(node_id)
        self.db_path = Path(db_path or Path.home() / ".openclaw" / "crdt.db")
        self._lock = threading.Lock()
        
        self._registers: Dict[str, LWWRegister] = {}
        self._counters: Dict[str, PNCounter] = {}
        self._sets: Dict[str, ORSet] = {}
        
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crdt_data (
                key TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def set(self, key: str, value: Any) -> Tuple[int, int, str]:
        """Set value with LWW Register."""
        with self._lock:
            if key not in self._registers:
                self._registers[key] = LWWRegister(self.node_id)
            
            self._registers[key].set(value)
            ts = self._registers[key].timestamp
            
            self._save_to_db(key, "register", self._registers[key].to_dict())
            logger.info(f"Set {key} with timestamp {ts}")
            return ts
    
    def get(self, key: str) -> Any:
        """Get value."""
        with self._lock:
            if key in self._registers:
                return self._registers[key].get()
            return None
    
    def increment(self, key: str, delta: int = 1) -> int:
        """Increment counter."""
        with self._lock:
            if key not in self._counters:
                self._counters[key] = PNCounter(self.node_id)
            
            self._counters[key].increment(delta)
            self._save_to_db(key, "counter", self._counters[key].to_dict())
            return self._counters[key].value()
    
    def decrement(self, key: str, delta: int = 1) -> int:
        """Decrement counter."""
        with self._lock:
            if key not in self._counters:
                self._counters[key] = PNCounter(self.node_id)
            
            self._counters[key].decrement(delta)
            self._save_to_db(key, "counter", self._counters[key].to_dict())
            return self._counters[key].value()
    
    def add_to_set(self, key: str, element: str):
        """Add element to set."""
        with self._lock:
            if key not in self._sets:
                self._sets[key] = ORSet(self.node_id)
            
            self._sets[key].add(element)
            self._save_to_db(key, "set", self._sets[key].to_dict())
    
    def remove_from_set(self, key: str, element: str):
        """Remove element from set."""
        with self._lock:
            if key in self._sets:
                self._sets[key].remove(element)
                self._save_to_db(key, "set", self._sets[key].to_dict())
    
    def get_set(self, key: str) -> Set[str]:
        """Get set elements."""
        with self._lock:
            if key in self._sets:
                return self._sets[key].get_all()
            return set()
    
    def merge(self, other_data: Dict[str, Any]):
        """Merge data from another node."""
        with self._lock:
            for key, data in other_data.items():
                crdt_type = data.get("type")
                crdt_data = data.get("data")
                
                if crdt_type == "register":
                    if key not in self._registers:
                        self._registers[key] = LWWRegister(self.node_id)
                    other = LWWRegister.from_dict(crdt_data)
                    self._registers[key].merge(other)
                
                elif crdt_type == "counter":
                    if key not in self._counters:
                        self._counters[key] = PNCounter(self.node_id)
                    other = PNCounter.from_dict(crdt_data)
                    self._counters[key].merge(other)
                
                elif crdt_type == "set":
                    if key not in self._sets:
                        self._sets[key] = ORSet(self.node_id)
                    other = ORSet.from_dict(crdt_data)
                    self._sets[key].merge(other)
                
                self._save_to_db(key, crdt_type, data["data"])
            
            logger.info(f"Merged {len(other_data)} keys")
    
    def export(self) -> Dict[str, Any]:
        """Export all data for syncing."""
        with self._lock:
            data = {}
            
            for key, reg in self._registers.items():
                data[key] = {"type": "register", "data": reg.to_dict()}
            
            for key, counter in self._counters.items():
                data[key] = {"type": "counter", "data": counter.to_dict()}
            
            for key, s in self._sets.items():
                data[key] = {"type": "set", "data": s.to_dict()}
            
            return data
    
    def _save_to_db(self, key: str, crdt_type: str, data: Dict):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO crdt_data (key, type, data, timestamp)
            VALUES (?, ?, ?, ?)
        """, (key, crdt_type, json.dumps(data), self.hlc.now()[0]))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    import sys
    
    manager = CRDTManager("node-1")
    
    if len(sys.argv) < 2:
        print("Usage: python crdt_manager.py <command>")
        print("Commands: set, get, incr, decr, add, remove, set-get, export")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "set":
        key = sys.argv[2]
        value = sys.argv[3]
        ts = manager.set(key, value)
        print(f"Set {key} with timestamp {ts}")
    
    elif cmd == "get":
        key = sys.argv[2]
        value = manager.get(key)
        print(f"Value: {value}")
    
    elif cmd == "incr":
        key = sys.argv[2]
        delta = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        value = manager.increment(key, delta)
        print(f"Counter: {value}")
    
    elif cmd == "export":
        data = manager.export()
        print(json.dumps(data, indent=2, default=str))
