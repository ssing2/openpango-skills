#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

try:
    import hvac
except ImportError:
    hvac = None

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("router")

# Determine workspace paths
WORKSPACE_DIR = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SESSIONS_DIR = WORKSPACE_DIR / "sessions"

class VaultClient:
    """Wrapper for hvac to dynamically resolve secrets using AppRole or Token auth."""
    def __init__(self):
        self.url = os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self.role_id = os.environ.get("VAULT_ROLE_ID")
        self.secret_id = os.environ.get("VAULT_SECRET_ID")
        self.token = os.environ.get("VAULT_TOKEN")
        self.client = None

        if hvac is None:
            logger.warning("Vault integration disabled: 'hvac' library not installed.")
            return

        try:
            self.client = hvac.Client(url=self.url)
            self._authenticate()
        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            self.client = None

    def _authenticate(self):
        if not self.client:
            return

        if self.role_id and self.secret_id:
            logger.info("Authenticating via Vault AppRole...")
            self.client.auth.approle.login(role_id=self.role_id, secret_id=self.secret_id)
        elif self.token:
            logger.info("Authenticating via Vault Token...")
            self.client.token = self.token
        
        if not self.client.is_authenticated():
            logger.error("Vault client failed to authenticate.")
            self.client = None

    def get_secret(self, path: str, key: str = None):
        """Fetches a secret from vault's KV v2 engine."""
        if not self.client:
            raise RuntimeError("Vault is not configured or authenticated.")
        
        try:
            read_response = self.client.secrets.kv.v2.read_secret_version(path=path)
            data = read_response['data']['data']
            if key:
                if key not in data:
                    raise KeyError(f"Key '{key}' not found in secret '{path}'")
                return data[key]
            return data
        except Exception as e:
            raise RuntimeError(f"Vault error reading {path}: {e}")

# Configure logging to console
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("router")

# Determine workspace paths
WORKSPACE_DIR = Path(os.environ.get("OPENCLAW_WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SESSIONS_DIR = WORKSPACE_DIR / "sessions"

def get_session_file(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"

def read_session(session_id: str) -> dict:
    file_path = get_session_file(session_id)
    if not file_path.exists():
        logger.error(f"Error: Session {session_id} not found.")
        sys.exit(1)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_session(session_id: str, data: dict):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = SESSIONS_DIR / f"{session_id}.json.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    temp_path.rename(get_session_file(session_id))

def cmd_spawn(args):
    """Spawns a new agent session."""
    session_id = str(uuid.uuid4())
    state = {
        "session_id": session_id,
        "agent_type": args.agent_type,
        "status": "idle",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "tasks": [],
        "outputs": []
    }
    write_session(session_id, state)
    print(session_id)

def cmd_status(args):
    """Checks the status of an active session."""
    state = read_session(args.session_id)
    print(state["status"])

def cmd_output(args):
    """Retrieves the accumulated output of a session."""
    state = read_session(args.session_id)
    print(json.dumps(state["outputs"], indent=2))

async def _process_task(session_id: str, task_payload: str):
    """Simulates background agent processing."""
    state = read_session(session_id)
    state["status"] = "processing"
    
    # Store the task payload
    task_id = str(uuid.uuid4())[:8]
    state["tasks"].append({"id": task_id, "payload": task_payload})
    write_session(session_id, state)
    
    # Simulate thinking/processing time (0.5 to 2 seconds for tests, typically longer)
    # Using a fast simulation so tests don't drag
    delay = float(os.environ.get("OPENCLAW_ROUTER_DELAY", "2.0"))
    await asyncio.sleep(delay)
    
    # Read state again in case it was modified
    state = read_session(session_id)
    
    # Generate mock output
    output_entry = {
        "task_id": task_id,
        "payload": task_payload,
        "result": f"Successfully processed task: {task_payload[:30]}...",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    state["outputs"].append(output_entry)
    state["status"] = "idle"  # Return to idle after processing
    write_session(session_id, state)

def _background_worker(session_id: str, task_payload: str):
    """Runs the asyncio event loop for background processing."""
    try:
        asyncio.run(_process_task(session_id, task_payload))
    except Exception as e:
        # If the background task fails, try to mark the session as failed
        try:
            state = read_session(session_id)
            state["status"] = "failed"
            state["error"] = str(e)
            write_session(session_id, state)
        except Exception:
            pass

def cmd_append(args):
    """Appends a task to a session and triggers background processing."""
    state = read_session(args.session_id)
    
    if state["status"] == "processing":
        logger.error(f"Error: Session {args.session_id} is already processing a task. Cannot append.")
        sys.exit(1)
        
    print(f"Task appended to session {args.session_id}")
    
    # If running in a test environment, we might want to block instead of fork
    if os.environ.get("OPENCLAW_SYNC_EXECUTION") == "1":
        _background_worker(args.session_id, args.task_payload)
        return

    # In a real environment, fork to run the task in the background so the CLI returns immediately
    pid = os.fork()
    if pid > 0:
        # Parent returns immediately to the caller
        sys.exit(0)
    else:
        # Child daemonizes and runs the task process
        os.setsid()
        # Redirect standard file descriptors to /dev/null
        devnull = os.open(os.devnull, os.O_RDWR)
        for i in range(3):
            try:
                os.dup2(devnull, i)
            except OSError:
                pass
        _background_worker(args.session_id, args.task_payload)
        sys.exit(0)

def cmd_resolve_secret(args):
    """Resolves a secret from Vault based on CLI arguments."""
    vault = VaultClient()
    try:
        val = vault.get_secret(args.path, args.key)
        if isinstance(val, dict):
            print(json.dumps(val, indent=2))
        else:
            print(val)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Orchestration Router (Manager Agent)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `resolve-secret`
    secret_parser = subparsers.add_parser("resolve-secret", help="Dynamically fetch a short-lived scoped API key from HashiCorp Vault")
    secret_parser.add_argument("path", help="Vault secret path (e.g., 'openpango/twitter')")
    secret_parser.add_argument("key", nargs="?", help="Specific JSON key to retrieve (optional)")

    # `spawn`
    spawn_parser = subparsers.add_parser("spawn", help="Spawn a new agent session")
    spawn_parser.add_argument("agent_type", help="Type of agent (e.g., coder, researcher)")

    # `append`
    append_parser = subparsers.add_parser("append", help="Append a task to an existing session")
    append_parser.add_argument("session_id", help="Session UUID")
    append_parser.add_argument("task_payload", help="JSON string or text payload for the task")

    # `status`
    status_parser = subparsers.add_parser("status", help="Get the status of a session")
    status_parser.add_argument("session_id", help="Session UUID")

    # `output`
    output_parser = subparsers.add_parser("output", help="Get the outputs of a session")
    output_parser.add_argument("session_id", help="Session UUID")

    args = parser.parse_args()

    if args.command == "spawn":
        cmd_spawn(args)
    elif args.command == "append":
        cmd_append(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "output":
        cmd_output(args)
    elif args.command == "resolve-secret":
        cmd_resolve_secret(args)

if __name__ == "__main__":
    main()
