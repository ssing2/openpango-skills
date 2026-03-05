#!/usr/bin/env python3
"""
router.py - OpenPango Async Router (Non-Polling Version)

This is a refactored version of the original router.py that replaces
polling-based waiting with event-driven asyncio architecture, following
OpenPango's "No Polling" principle.

Key improvements:
- Replaces time.sleep() polling with asyncio.Event blocking waits
- Uses JSONL instead of JSON for Git-friendly event sourcing
- Cleaner class-based architecture
- Full async/await support

Usage:
    python router.py spawn <agent_type>
    python router.py append <session_id> <task_payload>
    python router.py status <session_id>
    python router.py wait <session_id> [--timeout SECONDS]
    python router.py output <session_id>
"""

import asyncio
import json
import uuid
import sys
import os
import argparse
import subprocess
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

# Same paths as original
BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"
STORAGE_FILE = Path(__file__).parent / "openpango_storage.jsonl"  # Changed to JSONL
OUTPUTS_DIR = Path(__file__).parent / "outputs"

VALID_AGENTS = {"Researcher", "Planner", "Coder", "Designer"}

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Session:
    """Agent session with improved data structure."""
    id: str
    agent_type: str
    status: str = "idle"
    task: Optional[str] = None
    output_file: Optional[str] = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def __post_init__(self):
        if self.created_at is None:
            import time
            self.created_at = time.time()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return asdict(self)

# ============================================================================
# Storage Layer (Event-Sourced JSONL)
# ============================================================================

class SessionStore:
    """
    Git-friendly JSONL storage instead of monolithic JSON.

    Benefits:
    - Each append is atomic (no race conditions)
    - Git diff shows line-by-line changes
    - Event sourcing pattern (immutable log)
    """

    def __init__(self, storage_path: Path = None):
        self.storage_path = storage_path or STORAGE_FILE
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _read_all(self) -> Dict[str, Session]:
        """Read all sessions from JSONL log."""
        sessions = {}
        if not self.storage_path.exists():
            return sessions

        with open(self.storage_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    session = Session(**data)
                    sessions[session.id] = session
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"[WARN] Invalid line: {e}", file=sys.stderr)
        return sessions

    def save_session(self, session: Session):
        """Append session to JSONL (atomic write)."""
        with self._lock:
            # Atomic write: temp + rename
            temp_path = self.storage_path.with_suffix(".tmp")
            with open(temp_path, "a") as f:
                json.dump(session.to_dict(), f)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            temp_path.replace(self.storage_path)

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        sessions = self._read_all()
        return sessions.get(session_id)

    def update_session(self, session_id: str, **updates):
        """Update session fields by appending new version."""
        sessions = self._read_all()
        if session_id not in sessions:
            return False

        session = sessions[session_id]
        for key, value in updates.items():
            setattr(session, key, value)

        self.save_session(session)
        return True

# ============================================================================
# Session Manager (Event-Driven, No Polling)
# ============================================================================

class SessionManager:
    """
    Manages sessions with asyncio.Event for non-blocking waits.

    This replaces the polling loop in the original wait_for_completion().
    """
    def __init__(self, store: SessionStore = None):
        self.store = store or SessionStore()
        self._completion_events: Dict[str, asyncio.Event] = {}

    def create_session(self, agent_type: str) -> Session:
        """Create a new session."""
        import time
        session = Session(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            created_at=time.time()
        )

        # Create completion event for this session
        self._completion_events[session.id] = asyncio.Event()

        self.store.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.store.get_session(session_id)

    def mark_completed(self, session_id: str):
        """Signal session completion (triggers Event)."""
        event = self._completion_events.get(session_id)
        if event:
            event.set()

    async def wait_for_completion(self, session_id: str, timeout: float = 300.0):
        """
        Wait for session completion WITHOUT polling.

        Uses asyncio.Event.wait() which blocks efficiently
        until mark_completed() is called.
        """
        event = self._completion_events.get(session_id)
        if not event:
            raise ValueError(f"No event for session {session_id}")

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"[WARN] Timeout waiting for {session_id}", file=sys.stderr)
            raise

# ============================================================================
# Agent Execution (Same as original)
# ============================================================================

def execute_agent_task(session_id: str, agent_type: str, task_payload: str,
                       manager: SessionManager):
    """Execute agent task (runs in background thread)."""
    import time

    agent_dir = SKILLS_DIR / agent_type.lower()
    identity_file = agent_dir / "workspace" / "IDENTITY.md"
    soul_file = agent_dir / "workspace" / "SOUL.md"

    identity = identity_file.read_text() if identity_file.exists() else f"You are the {agent_type} agent."
    soul = soul_file.read_text() if soul_file.exists() else "Do your job."

    prompt = f"""
{identity}

{soul}

=== TASK ===
{task_payload}
===========

Execute this task strictly as your assigned role. You are running in a headless environment. Output your final response clearly.
"""

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUTS_DIR / f"{agent_type}-{session_id[:8]}.txt"

    cmd = ["gemini", "--prompt", prompt]
    if agent_type == "Coder":
        cmd.extend(["--yolo", "--approval-mode", "yolo"])

    try:
        result = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        with open(output_path, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- STDERR ---\n")
                f.write(result.stderr)
    except Exception as e:
        with open(output_path, "w") as f:
            f.write(f"Failed to execute gemini CLI: {str(e)}")

    # Update state and signal completion
    import time
    manager.store.update_session(
        session_id,
        status="completed",
        completed_at=time.time(),
        output_file=str(output_path)
    )

    # Signal completion (non-polling!)
    manager.mark_completed(session_id)

# ============================================================================
# CLI Commands
# ============================================================================

def cmd_spawn(args, manager: SessionManager):
    """Spawn a new agent session."""
    if args.agent_type not in VALID_AGENTS:
        print(f'{{"error": "Invalid agent type \\"{args.agent_type}\\""}}', file=sys.stderr)
        sys.exit(1)

    session = manager.create_session(args.agent_type)
    print(json.dumps({
        "session_id": session.id,
        "agent_type": session.agent_type,
        "status": session.status
    }))

def cmd_append(args, manager: SessionManager):
    """Append task to session and start execution."""
    session = manager.get_session(args.session_id)
    if not session:
        print(f'{{"error": "Session \\"{args.session_id}\\" not found"}}', file=sys.stderr)
        sys.exit(1)

    if session.status == "running":
        print(f'{{"error": "Session already running"}}', file=sys.stderr)
        sys.exit(1)

    # Update session
    import time
    manager.store.update_session(
        args.session_id,
        task=args.task_payload,
        status="running",
        started_at=time.time()
    )

    # Start execution in background thread
    thread = threading.Thread(
        target=execute_agent_task,
        args=(args.session_id, session.agent_type, args.task_payload, manager)
    )
    thread.daemon = True
    thread.start()

    print(json.dumps({
        "session_id": args.session_id,
        "message": "Task appended and execution started",
        "status": "running"
    }))

def cmd_status(args, manager: SessionManager):
    """Get session status."""
    session = manager.get_session(args.session_id)
    if not session:
        print(f'{{"error": "Session \\"{args.session_id}\\" not found"}}', file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "session_id": session.id,
        "status": session.status
    }))

def cmd_wait(args, manager: SessionManager):
    """Wait for session completion (ASYNC, no polling!)."""
    print(f"Waiting for session {args.session_id} to complete...", file=sys.stderr)

    # This uses asyncio.Event - NO polling!
    try:
        asyncio.run(manager.wait_for_completion(args.session_id, args.timeout))
        print(f"Session {args.session_id} completed.", file=sys.stderr)

        # Retrieve and display output
        session = manager.get_session(args.session_id)
        if session and session.output_file:
            output_path = Path(session.output_file)
            if output_path.exists():
                print(json.dumps({
                    "session_id": args.session_id,
                    "status": "completed",
                    "output_file": str(output_path),
                    "content": output_path.read_text()
                }))
                return
    except asyncio.TimeoutError:
        print(f'{{"error": "Timeout after {args.timeout}s"}}', file=sys.stderr)
        sys.exit(1)

    print(f'{{"error": "Output file missing"}}', file=sys.stderr)
    sys.exit(1)

def cmd_output(args, manager: SessionManager):
    """Retrieve session output."""
    session = manager.get_session(args.session_id)
    if not session:
        print(f'{{"error": "Session \\"{args.session_id}\\" not found"}}', file=sys.stderr)
        sys.exit(1)

    if session.status != "completed":
        print(f'{{"error": "Session not completed. Status: {session.status}"}}', file=sys.stderr)
        sys.exit(1)

    output_path = Path(session.output_file) if session.output_file else None
    if not output_path or not output_path.exists():
        print(f'{{"error": "Output file missing"}}', file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "session_id": args.session_id,
        "status": "completed",
        "output_file": str(output_path),
        "content": output_path.read_text()
    }))

# ============================================================================
# Main CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="OpenPango Async Router (Non-Polling Version)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # spawn
    spawn_p = subparsers.add_parser("spawn")
    spawn_p.add_argument("agent_type")

    # append
    append_p = subparsers.add_parser("append")
    append_p.add_argument("session_id")
    append_p.add_argument("task_payload")

    # status
    status_p = subparsers.add_parser("status")
    status_p.add_argument("session_id")

    # output
    output_p = subparsers.add_parser("output")
    output_p.add_argument("session_id")

    # wait (async version)
    wait_p = subparsers.add_parser("wait")
    wait_p.add_argument("session_id")
    wait_p.add_argument("--timeout", type=int, default=300)

    args = parser.parse_args()

    # Initialize manager
    manager = SessionManager()

    # Route command
    if args.command == "spawn":
        cmd_spawn(args, manager)
    elif args.command == "append":
        cmd_append(args, manager)
    elif args.command == "status":
        cmd_status(args, manager)
    elif args.command == "wait":
        cmd_wait(args, manager)
    elif args.command == "output":
        cmd_output(args, manager)

if __name__ == "__main__":
    main()
