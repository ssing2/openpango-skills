---
version: 1.0.0
name: browser
description: "Full-capability Playwright-based web automation."
user-invocable: true
metadata: {"openclaw":{"emoji":"🌐","skillKey":"openpango-browser"}}
---

## Cross-Skill Integration

This skill integrates with the Openpango ecosystem:
- **Orchestration**: Orchestration can delegate browser tasks to this skill.
- **Self-Improvement**: Errors encountered in the browser are logged by the self-improvement skill.
- **Persistent State**: Shared workspace files at `~/.openclaw/workspace/` (AGENTS.md, SOUL.md, TOOLS.md, .learnings/).
- **Real-time Coordination**: OpenClaw sessions API (sessions_send, sessions_spawn) referenced in orchestration SKILL.md.

# Browser Agent v3 - Full Web Automation

You have a full-featured browser that behaves like a natural user. It runs as a persistent daemon — the browser stays open between commands, preserving all state (cookies, sessions, modals, JavaScript-rendered content).

## Setup

**Always start the daemon first:**
```bash
python3 skills/browser/browser_daemon.py &
```
Wait 2-3 seconds for it to initialize, then use the client commands.

**Optional: Block ads/trackers for faster browsing:**
```bash
python3 skills/browser/browser_client.py block_urls preset
```

## The Interactive Read Loop (Your Primary Workflow)

The most powerful pattern is the **read -> decide -> act** loop:

### Step 1: Navigate
```bash
python3 skills/browser/browser_client.py goto "https://x.com/i/flow/signup"
```

### Step 2: Read the page (interactive mode)
```bash
python3 skills/browser/browser_client.py read
```
This returns a **numbered list** of every interactive element:
```
=== Interactive Elements ===
[1] Button: "Sign up with Google"
[2] Button: "Sign up with Apple"
[3] Link: "Create account" -> /i/flow/signup
[4] Input[text] name="name" placeholder="Name"
[5] Input[email] name="email" placeholder="Email"
[6] Input[password] name="password" placeholder="Password"
[7] Select name="month" selected="January" options=[January, February, March, April, May]
[8] Button: "Next"

=== Page Text ===
# Create your account
Join X today...

=== Iframe Content ===
[IFRAME: recaptcha]
I'm not a robot...
```

### Step 3: Act using index numbers OR fill entire form at once
```bash
# Option A: One field at a time
python3 skills/browser/browser_client.py type --index 4 "John Smith"
python3 skills/browser/browser_client.py type --index 5 "john@example.com"
python3 skills/browser/browser_client.py click --index 8

# Option B: Fill all fields at once (faster!)
python3 skills/browser/browser_client.py fill_form '{"input[name=\"name\"]": "John Smith", "input[name=\"email\"]": "john@example.com", "input[name=\"password\"]": "SecurePass123"}' --submit
```

### Step 4: Wait for the page to change, then read again
```bash
python3 skills/browser/browser_client.py wait_for_change --watch any --timeout 5000
python3 skills/browser/browser_client.py read
```

## Automatic Error Recovery

When any command fails, the daemon **automatically takes a screenshot** and includes the path in the error response:
```json
{
  "status": "error",
  "message": "Element not found",
  "error_screenshot": "/path/to/error_20260301_123456.png"
}
```
View the screenshot to understand what went wrong, then adjust your approach.

## Command Reference

### Navigation & Reading
| Command | Purpose |
|---------|---------|
| `goto <url>` | Navigate to URL |
| `read` | Interactive element map + iframe content (default) |
| `read --mode text` | Legacy markdown text extraction |
| `read --mode full` | Raw HTML including iframes |
| `read --selector ".modal"` | Read only within a container |
| `read --no-iframes` | Skip iframe content |
| `screenshot` | Full page screenshot |
| `screenshot --selector "#captcha"` | Screenshot a specific element |
| `screenshot --full-page` | Capture entire scrollable page |

### Interaction
| Command | Purpose |
|---------|---------|
| `click <selector>` | Click an element |
| `click --index N` | Click element N from interactive read |
| `click <selector> --double` | Double-click |
| `click <selector> --right` | Right-click |
| `type <selector> "text"` | Clear field and type |
| `type <selector> "text" --submit` | Type and press Enter |
| `type <selector> "text" --no-clear` | Append text without clearing |
| `type --index N "text"` | Type into element N from read |
| `select <selector> "Option Label"` | Select dropdown option |
| `fill_form '{"sel": "val", ...}'` | Fill entire form at once |
| `fill_form '...' --submit` | Fill form and press Enter |
| `hover <selector>` | Hover (trigger menus/tooltips) |
| `drag <source> <target>` | Drag and drop between elements |
| `keyboard Enter` | Press Enter |
| `keyboard Tab` | Press Tab |
| `keyboard Escape` | Press Escape |
| `keyboard Control+a` | Select all |
| `upload <selector> /path/to/file` | Upload file |

### Page Control
| Command | Purpose |
|---------|---------|
| `scroll down 500` | Scroll down 500px |
| `scroll up 1000` | Scroll up 1000px |
| `scroll --selector "#footer"` | Scroll to element |
| `wait ".loading" --state hidden` | Wait for element to disappear |
| `wait "#results" --state visible` | Wait for element to appear |
| `wait_for_change` | Wait until page content changes |
| `wait_for_change --watch url` | Wait specifically for URL change |
| `exec_js "document.title"` | Run JavaScript |

### Tab Management
| Command | Purpose |
|---------|---------|
| `tabs list` | Show all open tabs |
| `tabs switch 1` | Switch to tab at index 1 |
| `tabs new "https://..."` | Open URL in new tab |
| `tabs close 2` | Close tab at index 2 |

### Session Management
| Command | Purpose |
|---------|---------|
| `cookies list` | List all cookies |
| `cookies list --domain "x.com"` | Filter cookies by domain |
| `cookies clear` | Clear all cookies |
| `dialog accept` | Auto-accept next dialog |
| `dialog dismiss` | Auto-dismiss next dialog |

### Network & Performance
| Command | Purpose |
|---------|---------|
| `block_urls preset` | Block common ads/trackers (15 domains) |
| `block_urls add "**/*ads*/**"` | Block custom URL pattern |
| `block_urls list` | List all blocked patterns |
| `block_urls clear` | Remove all blocks |

### Debugging & Downloads
| Command | Purpose |
|---------|---------|
| `console_logs` | View browser console output |
| `console_logs --level error` | Show only JS errors |
| `console_logs --clear` | Read and clear the buffer |
| `download list` | List files downloaded this session |
| `download clear` | Clear download history |

## Anti-Detection

The browser includes automatic measures to appear natural:
- Realistic Chrome user-agent string
- `navigator.webdriver` set to undefined
- Automation flags removed (`--enable-automation` suppressed)
- Randomized viewport dimensions
- Natural-looking mouse movements with slight position jitter
- Randomized typing speed (40-100ms per keystroke)
- Patched permissions API and plugin count
- Persistent user data directory (cookies/localStorage survive restarts)

## Tips for AI Agents

1. **Always read before acting.** The interactive read gives you the exact selectors and index numbers you need.
2. **Use `fill_form` for multi-field forms** — it's faster and more reliable than typing into each field individually.
3. **Use `wait_for_change` instead of fixed sleeps** after submitting forms or clicking navigation elements.
4. **Use screenshots for visual content** — CAPTCHAs, images, complex layouts that DOM extraction misses.
5. **Check iframe content** in the read output — many auth flows (Google OAuth, reCAPTCHA) live inside iframes.
6. **Block ads/trackers first** with `block_urls preset` — pages load 2-5x faster.
7. **Check `console_logs --level error`** when something isn't working — JS errors often explain why.
8. **Tab management** is critical for OAuth flows that open popup windows.
9. **Auto error screenshots** — when a command fails, check the `error_screenshot` path in the response to see what went wrong.
10. **The `exec_js` command** is your escape hatch — if a specific interaction isn't covered, fall back to raw JavaScript.
11. **Downloads are automatic** — any file the browser downloads is saved to `.browser_data/downloads/`. Check with `download list`.

## Error Handling

Every command has automatic error screenshots. If a command returns `{"status": "error", ...}`:
1. Check the `error_screenshot` field — view the PNG to see the actual page state
2. Run `read` to re-assess the current interactive elements
3. Run `console_logs --level error` to check for JavaScript errors
4. The page may have changed (redirect, popup, SPA route change)
5. Try using `wait` or `wait_for_change` to ensure content has loaded
