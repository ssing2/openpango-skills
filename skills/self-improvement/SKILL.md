---
version: 1.0.0
name: self-improvement
description: "Captures learnings, proposes self-updates via git, and coordinates ecosystem growth."
user-invocable: true
metadata: {"openclaw":{"emoji":"📝","skillKey":"openpango-self-improvement"}}
---

## Cross-Skill Integration

This skill integrates with the Openpango ecosystem:
- **Browser**: Errors encountered in the browser are monitored and logged by this skill.
- **Memory**: Can create tasks in memory for tracking new learnings.
- **Orchestration**: Routing failures and errors are monitored and logged.
- **Persistent State**: Monitors all skills and uses shared workspace at `~/.openclaw/workspace/` (AGENTS.md, SOUL.md, TOOLS.md, .learnings/) for persistence.

# Self-Improvement Skill

This skill empowers the agent to continuously improve by combining structured learning logs and safe, git-sandboxed skill updates.

## Part A: Learnings Log

Log learnings and errors to markdown files for continuous improvement. Coding agents can later process these into fixes, and important learnings get promoted to project memory.

### Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `~/.openclaw/workspace/.learnings/ERRORS.md` |
| User corrects you | Log to `~/.openclaw/workspace/.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `~/.openclaw/workspace/.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `~/.openclaw/workspace/.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `~/.openclaw/workspace/.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `~/.openclaw/workspace/.learnings/LEARNINGS.md` with category `best_practice` |

### Detection Triggers

Automatically log when you notice:
- **Corrections**: "No, that's not right...", "Actually, it should be..."
- **Feature Requests**: "Can you also...", "I wish you could..."
- **Knowledge Gaps**: Documentation was outdated, API behavior differed from understanding.
- **Errors**: Command returns non-zero exit code, exception or stack trace.

### Logging Format Example (LEARNINGS.md)

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending
**Area**: frontend | backend | infra | tests | docs | config

### Summary
One-line description of what was learned

### Details
Full context: what happened, what was wrong, what's correct

### Suggested Action
Specific fix or improvement to make
```

### Promotion Workflow

When a learning is broadly applicable, promote it to shared workspace memory (`~/.openclaw/workspace/`):
- `AGENTS.md`: Agent-specific workflows, tool usage patterns, automation rules.
- `SOUL.md`: Behavioral guidelines, communication style, principles.
- `TOOLS.md`: Tool capabilities, usage patterns, integration gotchas.

### Periodic Review

Review `.learnings/` at natural breakpoints (e.g., before starting a major task). Resolve fixed items, promote applicable learnings, link related entries, and escalate recurring issues.

### Automatic Skill Extraction

When a learning is valuable enough to become a reusable skill, extract it using the provided helper:
```bash
./skills/self-improvement/scripts/extract-skill.sh skill-name
```
Then customize `SKILL.md` and update the learning's status.

---

## Part B: Git-Sandboxed Updates

When the agent wants to modify its own `SKILL.md` or scripts, it MUST use the `skill_updater.py` tool.

The `skill_updater.py` tool safely proposes updates to the agent's skills by creating a new Git branch and committing the changes, requiring manual operator approval to merge.

### Usage

```bash
python3 skills/self-improvement/skill_updater.py --target-file <path_to_file> --content-file <path_to_new_content> --message "<commit_message>"
```

- `--target-file`: The path to the file to update (e.g., `skills/orchestration/SKILL.md`). Must be within the current project directory.
- `--content-file`: Path to a temporary file containing the new content.
- `--message`: Commit message explaining the improvement.

### Workflow

1. Write the intended new content to a temporary file.
2. Run `skill_updater.py`.
3. The script will verify the git repository is clean.
4. It creates a new branch `agent-updates-YYYYMMDD-HHMMSS`.
5. It overwrites the target file with the content file.
6. It commits the changes and switches back to the original branch.
7. The agent notifies the user to manually review and merge the new branch.
