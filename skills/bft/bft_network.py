#!/usr/bin/env python3
"""
bft_network.py - Byzantine Fault Tolerant mesh network.
"""

import os
import json
import logging
import random
import hashlib
import threading
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger("BFT")


class BFTError(Exception):
    pass


class ConsensusState:
    """PBFT consensus states."""
    IDLE = "idle"
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    EXECUTED = "executed"


class Message:
    """BFT message."""
    
    def __init__(
        self,
        msg_type: str,
        node_id: str,
        view: int,
        sequence: int,
        digest: str,
        payload: Optional[Dict] = None
    ):
        self.msg_type = msg_type
        self.node_id = node_id
        self.view = view
        self.sequence = sequence
        self.digest = digest
        self.payload = payload or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "msg_type": self.msg_type,
            "node_id": self.node_id,
            "view": self.view,
            "sequence": self.sequence,
            "digest": self.digest,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        msg = cls(
            msg_type=data["msg_type"],
            node_id=data["node_id"],
            view=data["view"],
            sequence=data["sequence"],
            digest=data["digest"],
            payload=data.get("payload", {}),
        )
        msg.timestamp = data.get("timestamp", "")
        return msg


class BFTNode:
    """BFT node."""
    
    def __init__(self, node_id: str, is_primary: bool = False):
        self.node_id = node_id
        self.is_primary = is_primary
        self.view = 0
        self.sequence = 0
        self.state = ConsensusState.IDLE
        self.message_log: List[Message] = []
        self.prepare_messages: Dict[str, Set[str]] = defaultdict(set)
        self.commit_messages: Dict[str, Set[str]] = defaultdict(set)
        self.executed: Set[str] = set()
    
    def reset(self):
        self.state = ConsensusState.IDLE
        self.message_log = []
        self.prepare_messages = defaultdict(set)
        self.commit_messages = defaultdict(set)


class BFTNetwork:
    """
    Byzantine Fault Tolerant mesh network.
    
    Implements PBFT consensus for agent coordination.
    """
    
    def __init__(
        self,
        node_id: str,
        nodes: Optional[List[str]] = None,
        f: int = 1
    ):
        """
        Initialize BFT network.
        
        Args:
            node_id: This node's ID
            nodes: List of all node IDs
            f: Maximum number of Byzantine nodes
        """
        self.node_id = node_id
        self.nodes = nodes or [node_id]
        self.f = f  # Max Byzantine nodes
        
        # Minimum nodes for BFT: 3f + 1
        self.min_nodes = 3 * f + 1
        
        self.node = BFTNode(node_id, node_id == self.nodes[0])
        self.pending_tasks: Dict[str, Dict] = {}
        self.results: Dict[str, Any] = {}
        
        self._lock = threading.Lock()
        self._running = False
        
        # Message handlers
        self.handlers = {
            "pre_prepare": self._handle_pre_prepare,
            "prepare": self._handle_prepare,
            "commit": self._handle_commit,
        }
    
    def start(self):
        """Start the BFT network."""
        self._running = True
        logger.info(f"BFT network started: {self.node_id}")
    
    def stop(self):
        """Stop the BFT network."""
        self._running = False
        logger.info(f"BFT network stopped: {self.node_id}")
    
    def is_primary(self) -> bool:
        """Check if this node is primary."""
        return self.node.view % len(self.nodes) == self.nodes.index(self.node_id)
    
    def propose(self, task_id: str, task: Dict) -> bool:
        """
        Propose a task for consensus.
        
        Args:
            task_id: Task ID
            task: Task data
            
        Returns:
            Success status
        """
        with self._lock:
            if not self.is_primary():
                logger.warning("Only primary can propose")
                return False
            
            self.node.sequence += 1
            
            # Create digest
            digest = self._compute_digest(task_id, task)
            
            # Create pre-prepare message
            msg = Message(
                msg_type="pre_prepare",
                node_id=self.node_id,
                view=self.node.view,
                sequence=self.node.sequence,
                digest=digest,
                payload={"task_id": task_id, "task": task}
            )
            
            self.pending_tasks[digest] = {"task_id": task_id, "task": task}
            self.node.message_log.append(msg)
            
            logger.info(f"Proposed task {task_id} with digest {digest[:8]}")
            
            # Simulate broadcast (in real implementation, send to network)
            return True
    
    def _compute_digest(self, task_id: str, task: Dict) -> str:
        """Compute task digest."""
        data = json.dumps({"task_id": task_id, "task": task}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def receive_message(self, message: Message):
        """
        Receive a message from another node.
        
        Args:
            message: The message
        """
        with self._lock:
            handler = self.handlers.get(message.msg_type)
            if handler:
                handler(message)
            else:
                logger.warning(f"Unknown message type: {message.msg_type}")
    
    def _handle_pre_prepare(self, msg: Message):
        """Handle pre-prepare message."""
        if msg.view != self.node.view:
            return
        
        # Verify primary
        expected_primary = self.nodes[msg.view % len(self.nodes)]
        if msg.node_id != expected_primary:
            logger.warning(f"Invalid primary: {msg.node_id}")
            return
        
        # Store pending task
        if msg.digest not in self.pending_tasks:
            self.pending_tasks[msg.digest] = msg.payload
        
        # Send prepare
        prepare_msg = Message(
            msg_type="prepare",
            node_id=self.node_id,
            view=msg.view,
            sequence=msg.sequence,
            digest=msg.digest,
        )
        
        self.node.message_log.append(prepare_msg)
        logger.debug(f"Sent prepare for {msg.digest[:8]}")
    
    def _handle_prepare(self, msg: Message):
        """Handle prepare message."""
        if msg.view != self.node.view:
            return
        
        self.node.prepare_messages[msg.digest].add(msg.node_id)
        
        # Check if we have 2f prepares
        if len(self.node.prepare_messages[msg.digest]) >= 2 * self.f:
            # Send commit
            commit_msg = Message(
                msg_type="commit",
                node_id=self.node_id,
                view=msg.view,
                sequence=msg.sequence,
                digest=msg.digest,
            )
            
            self.node.message_log.append(commit_msg)
            logger.debug(f"Sent commit for {msg.digest[:8]}")
    
    def _handle_commit(self, msg: Message):
        """Handle commit message."""
        if msg.view != self.node.view:
            return
        
        self.node.commit_messages[msg.digest].add(msg.node_id)
        
        # Check if we have 2f+1 commits
        if len(self.node.commit_messages[msg.digest]) >= 2 * self.f + 1:
            if msg.digest not in self.node.executed:
                self._execute(msg.digest)
    
    def _execute(self, digest: str):
        """Execute a committed task."""
        if digest in self.pending_tasks:
            task_data = self.pending_tasks[digest]
            task_id = task_data.get("task_id")
            task = task_data.get("task", {})
            
            # Execute task (placeholder)
            result = self._execute_task(task)
            
            self.results[task_id] = result
            self.node.executed.add(digest)
            
            logger.info(f"Executed task {task_id}: {result}")
    
    def _execute_task(self, task: Dict) -> Any:
        """Execute a task (placeholder)."""
        action = task.get("action", "unknown")
        data = task.get("data", [])
        
        # Simulate task execution
        if action == "compute":
            return {"status": "computed", "result": sum(data) if data else 0}
        elif action == "store":
            return {"status": "stored", "items": len(data)}
        else:
            return {"status": "unknown"}
    
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get result for a task."""
        with self._lock:
            return self.results.get(task_id)
    
    def add_node(self, node_id: str):
        """Add a node to the network."""
        with self._lock:
            if node_id not in self.nodes:
                self.nodes.append(node_id)
                logger.info(f"Added node: {node_id}")
    
    def remove_node(self, node_id: str):
        """Remove a node from the network."""
        with self._lock:
            if node_id in self.nodes:
                self.nodes.remove(node_id)
                logger.info(f"Removed node: {node_id}")
    
    def view_change(self):
        """Initiate view change."""
        with self._lock:
            self.node.view += 1
            self.node.is_primary = self.is_primary()
            self.node.reset()
            
            logger.info(f"View change to {self.node.view}, primary: {self.node.is_primary}")
    
    def get_status(self) -> Dict:
        """Get network status."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "view": self.node.view,
                "sequence": self.node.sequence,
                "state": self.node.state,
                "is_primary": self.node.is_primary,
                "nodes": len(self.nodes),
                "pending_tasks": len(self.pending_tasks),
                "executed": len(self.node.executed),
            }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bft_network.py <command>")
        print("Commands: start, propose, status")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "start":
        node_id = sys.argv[2] if len(sys.argv) > 2 else "node-1"
        nodes = ["node-1", "node-2", "node-3", "node-4"]
        network = BFTNetwork(node_id, nodes)
        network.start()
        print(json.dumps(network.get_status(), indent=2))
    
    elif cmd == "propose":
        node_id = sys.argv[2] if len(sys.argv) > 2 else "node-1"
        nodes = ["node-1", "node-2", "node-3", "node-4"]
        network = BFTNetwork(node_id, nodes)
        network.start()
        
        task_id = "task-1"
        task = {"action": "compute", "data": [1, 2, 3]}
        result = network.propose(task_id, task)
        print(f"Proposed: {result}")
    
    elif cmd == "status":
        node_id = sys.argv[2] if len(sys.argv) > 2 else "node-1"
        network = BFTNetwork(node_id)
        print(json.dumps(network.get_status(), indent=2))
