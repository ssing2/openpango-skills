#!/usr/bin/env python3
"""
promote.py - Promote verified learnings to global OpenClaw workspace config.

Appends a verified learning summary to one of the global config files
(AGENTS.md, SOUL.md, TOOLS.md) and updates the original learning entry's
status to 'promoted'.

Usage:
    python3 promote.py --learning-id LRN-20260303-001 --target AGENTS.md --summary "Always use --force flag for stale lockfiles"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_DIR = Path.home() / ".openclaw" / "workspace"
LEARNINGS_DIR = WORKSPACE_DIR / ".learnings"

VALID_TARGETS = ["AGENTS.md", "SOUL.md", "TOOLS.md"]
LEARNINGS_FILES = ["LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"]


def find_and_update_learning(learning_id: str, target: str) -> bool:
    """Find a learning entry by ID across all learnings files and update its status."""
    for filename in LEARNINGS_FILES:
        filepath = LEARNINGS_DIR / filename
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")
        # Match the entry header pattern: ## [LRN-20260303-001] category
        pattern = rf"(\*\*Status\*\*: )(\w+)"
        
        # Check if this file contains the learning ID
        if f"[{learning_id}]" not in content:
            continue

        # Find the section for this ID and update its status
        lines = content.split("\n")
        in_target_section = False
        updated = False

        for i, line in enumerate(lines):
            if f"[{learning_id}]" in line:
                in_target_section = True
                continue
            
            if in_target_section and line.startswith("**Status**:"):
                lines[i] = f"**Status**: promoted"
                updated = True
                break
            
            # If we hit the next entry header, stop
            if in_target_section and line.startswith("## ["):
                break

        if updated:
            filepath.write_text("\n".join(lines), encoding="utf-8")
            return True

    return False


def promote_learning(learning_id: str, target: str, summary: str) -> dict:
    """Promote a learning to a global config file."""
    target_path = WORKSPACE_DIR / target
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build the promotion entry
    entry = f"\n## [{learning_id}] — Promoted {timestamp}\n{summary}\n"

    # Ensure the target file exists
    if not target_path.exists():
        target_path.write_text(f"# {target.replace('.md', '')}\n\n", encoding="utf-8")

    # Append the promoted entry
    with open(target_path, "a", encoding="utf-8") as f:
        f.write(entry)

    # Update the original learning entry status
    status_updated = find_and_update_learning(learning_id, target)

    return {
        "status": "success",
        "learning_id": learning_id,
        "promoted_to": str(target_path),
        "original_updated": status_updated,
        "summary": summary,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Promote verified learnings to global OpenClaw workspace config."
    )
    parser.add_argument("--learning-id", required=True,
                        help="The ID of the learning to promote (e.g., LRN-20260303-001)")
    parser.add_argument("--target", required=True, choices=VALID_TARGETS,
                        help="Target global config file")
    parser.add_argument("--summary", required=True,
                        help="One-line summary to append to the target file")

    args = parser.parse_args()

    result = promote_learning(args.learning_id, args.target, args.summary)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
