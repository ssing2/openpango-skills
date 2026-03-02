#!/usr/bin/env python3
"""
agent_registry.py - Agent capability registration and discovery.

Provides a persistent registry for agents to register their capabilities
and discover other agents in the A2A network.
"""
import argparse
import json
import os
import sys
import uuid
import fcntl
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# Registry storage path
WORKSPACE_PATH = Path.home() / ".opеnclaw" / "workspace"
REGISTRY_FILE = WORKSPACE_PATH / "agent_registry.json"


def _ensure_registry():
    """Ensure registry file exists."""
    WORKSPACE_PATH.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "w") as f:
            json.dump({"agents": {}, "version": "1.0"}, f, indent=2)
            

def _load_registry() -> Dict:
    """Load registry with file locking."""
    _ensure_registry()
    with open(REGISTRY_FILE, "r") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            

def _save_registry(data: Dict):
    """Save registry with file locking."""
    _ensure_registry()
    with open(REGISTRY_FILE, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            

def register(agent_id: str = None, name: str = None, 
             capabilities: List[str] = None, metadata: Dict = None) -> Dict:
    """
    Register an agent with its capabilities.
    
    Args:
        agent_id: Unique agent identifier (auto-generated if not provided)
        name: Human-readable agent name
        capabilities: List of capability strings (e.g., ["coding", "research"])
        metadata: Additional metadata
        
    Returns:
        Registration result with agent_id
    """
    if agent_id is None:
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        
    registry = _load_registry()
    
    agent_info = {
        "id": agent_id,
        "name": name or agent_id,
        "capabilities": capabilities or [],
        "metadata": metadata or {},
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "status": "online"
    }
    
    # Update if exists, otherwise create
    if agent_id in registry["agents"]:
        agent_info["registered_at"] = registry["agents"][agent_id]["registered_at"]
        
    registry["agents"][agent_id] = agent_info
    _save_registry(registry)
    
    return {
        "status": "registered",
        "agent_id": agent_id,
        "name": agent_info["name"],
        "capabilities": agent_info["capabilities"]
    }
    

def unregister(agent_id: str) -> Dict:
    """Unregister an agent."""
    registry = _load_registry()
    
    if agent_id not in registry["agents"]:
        return {"error": f"Agent {agent_id} not found"}
        
    del registry["agents"][agent_id]
    _save_registry(registry)
    
    return {"status": "unregistered", "agent_id": agent_id}
    

def update_status(agent_id: str, status: str) -> Dict:
    """Update agent status (online/offline/busy)."""
    registry = _load_registry()
    
    if agent_id not in registry["agents"]:
        return {"error": f"Agent {agent_id} not found"}
        
    registry["agents"][agent_id]["status"] = status
    registry["agents"][agent_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
    _save_registry(registry)
    
    return {"status": "updated", "agent_id": agent_id, "new_status": status}
    

def discover(capability: str = None, status: str = None) -> Dict:
    """
    Discover agents by capability or status.
    
    Args:
        capability: Filter by capability (optional)
        status: Filter by status (optional)
        
    Returns:
        List of matching agents
    """
    registry = _load_registry()
    agents = list(registry["agents"].values())
    
    if capability:
        agents = [a for a in agents if capability in a.get("capabilities", [])]
        
    if status:
        agents = [a for a in agents if a.get("status") == status]
        
    return {
        "count": len(agents),
        "agents": agents
    }
    

def get_agent(agent_id: str) -> Dict:
    """Get agent details by ID."""
    registry = _load_registry()
    
    if agent_id not in registry["agents"]:
        return {"error": f"Agent {agent_id} not found"}
        
    return registry["agents"][agent_id]
    

def list_all() -> Dict:
    """List all registered agents."""
    registry = _load_registry()
    agents = list(registry["agents"].values())
    
    return {
        "count": len(agents),
        "agents": agents
    }
    

def heartbeat(agent_id: str) -> Dict:
    """Update agent last_seen timestamp."""
    registry = _load_registry()
    
    if agent_id not in registry["agents"]:
        return {"error": f"Agent {agent_id} not found"}
        
    registry["agents"][agent_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
    _save_registry(registry)
    
    return {"status": "ok", "agent_id": agent_id}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A2A Agent Registry")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register
    reg_parser = subparsers.add_parser("register", help="Register an agent")
    reg_parser.add_argument("--id", help="Agent ID (auto-generated if not provided)")
    reg_parser.add_argument("--name", help="Agent name")
    reg_parser.add_argument("--capabilities", nargs="*", default=[], help="Agent capabilities")
    reg_parser.add_argument("--metadata", help="JSON metadata")
    
    # Unregister
    unreg_parser = subparsers.add_parser("unregister", help="Unregister an agent")
    unreg_parser.add_argument("id", help="Agent ID")
    
    # Discover
    disc_parser = subparsers.add_parser("discover", help="Discover agents")
    disc_parser.add_argument("--capability", help="Filter by capability")
    disc_parser.add_argument("--status", help="Filter by status")
    
    # Get
    get_parser = subparsers.add_parser("get", help="Get agent details")
    get_parser.add_argument("id", help="Agent ID")
    
    # List
    subparsers.add_parser("list", help="List all agents")
    
    # Heartbeat
    hb_parser = subparsers.add_parser("heartbeat", help="Send heartbeat")
    hb_parser.add_argument("id", help="Agent ID")
    
    # Update status
    status_parser = subparsers.add_parser("status", help="Update agent status")
    status_parser.add_argument("id", help="Agent ID")
    status_parser.add_argument("status", choices=["online", "offline", "busy"])
    
    args = parser.parse_args()
    
    if args.command == "register":
        metadata = json.loads(args.metadata) if args.metadata else {}
        result = register(args.id, args.name, args.capabilities, metadata)
    elif args.command == "unregister":
        result = unregister(args.id)
    elif args.command == "discover":
        result = discover(args.capability, args.status)
    elif args.command == "get":
        result = get_agent(args.id)
    elif args.command == "list":
        result = list_all()
    elif args.command == "heartbeat":
        result = heartbeat(args.id)
    elif args.command == "status":
        result = update_status(args.id, args.status)
        
    print(json.dumps(result, indent=2))
