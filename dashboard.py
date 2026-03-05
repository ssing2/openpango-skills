#!/usr/bin/env python3
"""
dashboard.py - OpenPango CLI Dashboard

A rich terminal UI for monitoring and managing OpenPango skills.
Built with Textual and Rich.

Usage:
    python dashboard.py
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, DataTable,
    Log, Button, ProgressBar, Placeholder
)
from textual.reactive import reactive
from pathlib import Path
import time
import json
from typing import Any, Dict, List


class SkillStatusTable(DataTable):
    """Displays status of all OpenPango skills."""

    def __init__(self):
        super().__init__()
        self.columns = [
            "Skill",
            "Status",
            "Uptime",
            "Sessions",
            "Health"
        ]

    def on_mount(self):
        """Initialize with skill data."""
        self.refresh()

    def refresh(self):
        """Refresh skill status data."""
        # Clear existing rows
        self.clear()

        # Add skill rows
        skills = self._get_skills()
        for skill in skills:
            self.add_row(
                skill["name"],
                "✓" if skill["healthy"] else "✗",
                f"{skill.get('uptime', 0)}s",
                str(skill.get('sessions', 0)),
                "OK" if skill["healthy"] else "ERROR"
            )

    def _get_skills(self) -> List[Dict]:
        """Get skill status from OpenPango."""
        # This would integrate with actual OpenPango status
        return [
            {"name": "browser", "healthy": True, "uptime": 3600, "sessions": 3},
            {"name": "memory", "healthy": True, "uptime": 3600, "sessions": 1},
            {"name": "orchestration", "healthy": True, "uptime": 3600, "sessions": 5},
            {"name": "hitl", "healthy": True, "uptime": 3600, "sessions": 0},
        ]


class SessionList(DataTable):
    """Displays active agent sessions."""

    def __init__(self):
        super().__init__()
        self.columns = [
            "Session ID",
            "Agent",
            "Status",
            "Created",
            "Task"
        ]

    def on_mount(self):
        """Initialize with session data."""
        self.refresh()

    def refresh(self):
        """Refresh session data."""
        self.clear()

        sessions = self._get_sessions()
        for session in sessions:
            self.add_row(
                session["id"][:8],
                session["agent_type"],
                session["status"],
                session["created"],
                session.get("task", "N/A")[:30]
            )

    def _get_sessions(self) -> List[Dict]:
        """Get sessions from OpenPango storage."""
        # This would read from sessions.jsonl
        return [
            {
                "id": "abc123def456",
                "agent_type": "Researcher",
                "status": "running",
                "created": "2m ago",
                "task": "Investigate AI trends"
            },
        ]


class SystemMonitor(Static):
    """Displays system resource usage."""

    def render(self) -> str:
        """Render system stats."""
        return """
┌─ System Resources ─────────────────┐
│ CPU: ████░░░░░ 15%                │
│ Memory: ██████░░░ 60% (4.8GB/8GB)  │
│ Disk: ██░░░░░░░░ 25%               │
│ Uptime: 2h 34m                    │
└────────────────────────────────────┘
        """.strip()


class OpenPangoDashboard(App):
    """
    OpenPango CLI Dashboard

    Rich terminal UI for monitoring skills, sessions, and logs.
    """

    CSS = """
    Screen {
        layout: vertical;
    }
    #skills_panel {
        height: 40%;
    }
    #sessions_panel {
        height: 30%;
    }
    #logs_panel {
        height: 25%;
    }
    DataTable {
        background: $primary;
    }
    """

    TITLE = "🦔 OpenPango Dashboard"
    SUB_TITLE = "Real-time monitoring"

    def compose(self) -> ComposeResult:
        """Compose dashboard widgets."""
        yield Header()
        yield Horizontal(
            Vertical(
                Static("📊 Skills Status", classes="header"),
                SkillStatusTable(id="skills_table"),
                id="skills_panel"
            ),
            Vertical(
                Static("🤖 Active Sessions", classes="header"),
                SessionList(id="sessions_table"),
                id="sessions_panel"
            ),
        )
        yield SystemMonitor()
        yield Vertical(
            Static("📋 Activity Log", classes="header"),
            Log(id="activity_log"),
            id="logs_panel"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        self.refresh_all()

    def refresh_all(self) -> None:
        """Refresh all data sources."""
        skills_table = self.query_one("#skills_table", SkillStatusTable)
        sessions_table = self.query_one("#sessions_table", SessionList)

        if skills_table:
            skills_table.refresh()
        if sessions_table:
            sessions_table.refresh()

        self.log_entry("Dashboard refreshed", "info")

    def log_entry(self, message: str, level: str = "info") -> None:
        """Add entry to activity log."""
        log = self.query_one("#activity_log", Log)
        if log:
            timestamp = time.strftime("%H:%M:%S")
            log.write_line(f"[{timestamp}] {message}")

    def action_refresh(self) -> None:
        """Refresh all data (bound to 'r' key)."""
        self.refresh_all()


if __name__ == "__main__":
    app = OpenPangoDashboard()
    app.run()
