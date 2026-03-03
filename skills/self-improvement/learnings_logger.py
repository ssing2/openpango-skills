#!/usr/bin/env python3
"""
learnings_logger.py - Automated Learnings Logger for OpenClaw Self-Improvement.

Programmatically creates structured learning entries in ~/.openclaw/workspace/.learnings/
Supports logging errors, learnings (corrections/insights/best practices), and feature requests.

Usage:
    python3 learnings_logger.py log-error --summary "npm ERR! missing script" --area backend
    python3 learnings_logger.py log-learning --summary "Use --force for stale locks" --category best_practice --area infra
    python3 learnings_logger.py log-feature-request --summary "Add caching layer to API" --area backend
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
LEARNINGS_DIR = WORKSPACE_DIR / ".learnings"

# File mapping for each log type
LOG_FILES = {
    "log-error": "ERRORS.md",
    "log-learning": "LEARNINGS.md",
    "log-feature-request": "FEATURE_REQUESTS.md",
}

# ID prefix mapping
ID_PREFIXES = {
    "log-error": "ERR",
    "log-learning": "LRN",
    "log-feature-request": "FR",
}


def ensure_directories():
    """Create workspace and learnings directories if they don't exist."""
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)


def generate_id(prefix: str, log_file: Path) -> str:
    """Generate a unique sequential ID for a log entry (e.g., ERR-20260303-001)."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    base = f"{prefix}-{date_str}-"

    # Count existing entries for today to determine sequence number
    seq = 1
    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        # Count how many entries with today's date prefix exist
        while f"## [{base}{seq:03d}]" in content:
            seq += 1

    return f"{base}{seq:03d}"


def ensure_file_header(filepath: Path, title: str):
    """Create the log file with a standard header if it doesn't exist."""
    if not filepath.exists():
        header = f"# {title}\n\n"
        filepath.write_text(header, encoding="utf-8")


def log_entry(log_type: str, summary: str, details: str = "",
              category: str = "", area: str = "general",
              priority: str = "medium", action: str = "") -> dict:
    """Create and append a structured log entry to the appropriate file."""
    ensure_directories()

    filename = LOG_FILES[log_type]
    prefix = ID_PREFIXES[log_type]
    filepath = LEARNINGS_DIR / filename

    # Set up file header based on type
    titles = {
        "log-error": "Errors Log",
        "log-learning": "Learnings",
        "log-feature-request": "Feature Requests",
    }
    ensure_file_header(filepath, titles[log_type])

    entry_id = generate_id(prefix, filepath)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build the markdown entry
    lines = []

    if log_type == "log-error":
        lines.append(f"\n## [{entry_id}] error\n")
    elif log_type == "log-learning":
        cat = category if category else "insight"
        lines.append(f"\n## [{entry_id}] {cat}\n")
    elif log_type == "log-feature-request":
        lines.append(f"\n## [{entry_id}] feature_request\n")

    lines.append(f"**Logged**: {timestamp}")
    lines.append(f"**Priority**: {priority}")
    lines.append("**Status**: pending")
    lines.append(f"**Area**: {area}")
    lines.append("")
    lines.append("### Summary")
    lines.append(summary)
    lines.append("")

    if details:
        lines.append("### Details")
        lines.append(details)
        lines.append("")

    if action:
        lines.append("### Suggested Action")
        lines.append(action)
        lines.append("")

    lines.append("---\n")

    entry_text = "\n".join(lines)

    # Append to the file
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(entry_text)

    return {
        "status": "success",
        "id": entry_id,
        "file": str(filepath),
        "type": log_type,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Self-Improvement Learnings Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Log type")

    # Common arguments for all subcommands
    def add_common_args(sub):
        sub.add_argument("--summary", required=True, help="One-line description")
        sub.add_argument("--details", default="", help="Full context and details")
        sub.add_argument("--area", default="general",
                         choices=["frontend", "backend", "infra", "tests", "docs", "config", "general"],
                         help="Area of the codebase affected")
        sub.add_argument("--priority", default="medium",
                         choices=["low", "medium", "high", "critical"],
                         help="Priority level")
        sub.add_argument("--action", default="", help="Suggested fix or improvement")

    # log-error subcommand
    error_parser = subparsers.add_parser("log-error", help="Log an error or failure")
    add_common_args(error_parser)

    # log-learning subcommand
    learning_parser = subparsers.add_parser("log-learning", help="Log a learning or insight")
    add_common_args(learning_parser)
    learning_parser.add_argument("--category", default="insight",
                                 choices=["correction", "insight", "knowledge_gap", "best_practice"],
                                 help="Type of learning")

    # log-feature-request subcommand
    fr_parser = subparsers.add_parser("log-feature-request", help="Log a feature request")
    add_common_args(fr_parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    result = log_entry(
        log_type=args.command,
        summary=args.summary,
        details=args.details,
        category=getattr(args, "category", ""),
        area=args.area,
        priority=args.priority,
        action=args.action,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
