# Dashboard Skill

**Version:** 1.0.0
**Author:** 昕昕昶 (AI Agent)
**Description:** Rich CLI dashboard for monitoring OpenPango skills

---

## 🎯 Purpose

Provides a terminal-based monitoring dashboard for OpenPango skills,
showing real-time status of skills, active sessions, and system resources.

---

## 🚀 Usage

### Start dashboard
```bash
python dashboard.py
```

### Interactive commands
- `r` - Refresh data
- `q` - Quit
- `Tab` - Navigate between panels

---

## 📊 Features

- **Skill Status Table**
  - Health check for all skills
  - Uptime tracking
  - Active session count

- **Session List**
  - Active agent sessions
  - Session status (running, idle, completed)
  - Task descriptions

- **System Monitor**
  - CPU usage
  - Memory usage
  - Disk usage
  - Uptime

- **Activity Log**
  - Real-time event stream
  - Timestamped entries
  - Color-coded by level

---

## 🎨 UI Layout

```
┌─────────────────────────────────────────────┐
│         🦔 OpenPango Dashboard              │
├─────────────────┬───────────────────────────┤
│ 📊 Skills Status│ 🤖 Active Sessions        │
│ ┌─────────────┐│ ┌─────────────────────┐   │
│ │ browser ✓  ││ │ #123 Researcher    │   │
│ │ memory ✓   ││ │ #124 Coder         │   │
│ │ hitl ✓     ││ │ #125 Planner       │   │
│ └─────────────┘│ └─────────────────────┘   │
├─────────────────┴───────────────────────────┤
│ ┌─ System Resources ───────────────────┐   │
│ │ CPU: ████░░░░░ 15%                    │   │
│ │ Memory: ██████░░░ 60%                 │   │
│ └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ 📋 Activity Log                           │
│ [12:30:01] Session #123 started            │
│ [12:30:05] Task appended                   │
│ [12:30:10] Research completed              │
└─────────────────────────────────────────────┘
```

---

## 🔧 Requirements

- Python 3.8+
- textual >= 0.44.0
- rich >= 13.0.0

### Install dependencies
```bash
pip install textual rich
```

---

## 🧪 Testing

```bash
# Run dashboard
python dashboard.py

# Expected: Rich TUI opens with skill status
```

---

## 📖 Integration

### With OpenPango CLI
```bash
# Add as OpenPango command
openpango dashboard

# Or standalone
python skills/dashboard/dashboard.py
```

### Data sources
- `~/.openclaw/workspace/sessions.jsonl` - Session data
- `~/.openclaw/skills/` - Skill symlinks
- System resources via `psutil`

---

## ⚠️ Limitations

1. Requires terminal with color support
2. Not suitable for headless environments
3. Manual refresh (no auto-update in this version)

---

## 🎁 Future Enhancements

- Auto-refresh interval
- Interactive session management
- Skill start/stop controls
- Historical charts
- Filtering and search

---

*Part of OpenPango Skills Suite*
*Bounty #167: CLI Dashboard with Rich Terminal UI*
