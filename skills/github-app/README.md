# GitHub App Native Integration for OpenPango Skills

Official GitHub App backend that enables autonomous code review and bug fixes through webhook-triggered OpenClaw tasks.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   export GITHUB_APP_ID="your_app_id"
   export GITHUB_APP_SECRET="your_app_secret"
   export WEBHOOK_SECRET="your_webhook_secret"
   export GITHUB_PRIVATE_KEY="$(cat private-key.pem)"
   export OPENCLAW_API_URL="http://localhost:3000"
   ```

3. Run server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

## Project Structure

```
skills/github-app/
├── app.py                 # FastAPI main application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── SKILL.md              # Documentation
├── README.md             # This file
├── webhook/
│   ├── signature.py      # Webhook signature verification
│   └── router.py         # Event routing
├── services/
│   ├── pr_reviewer.py    # PR code review service
│   ├── issue_handler.py  # Issue command parser
│   └── safety.py         # Permission scoping
├── tasks/
│   └── dispatcher.py     # OpenClaw task dispatcher (TODO)
└── test_safety.py        # Safety tests
```

## Features

- ✅ Webhook receiver with signature verification
- ✅ Event routing (PR, issue, push events)
- ✅ PR code review automation
- ✅ Issue command handler (@openpango commands)
- ✅ Safety checks and branch protection
- ✅ Audit logging
- ⏳ OpenClaw task dispatcher (in progress)

## Testing

```bash
# Run all tests
pytest test_safety.py -v

# Run with coverage
pytest --cov=. test_safety.py
```

## API Documentation

Access interactive API docs at: `http://localhost:8000/docs`

## Security

- All webhooks verified with HMAC-SHA256
- Branch protection enforced
- Minimal permission requests
- Comprehensive audit logging

## Status

**Development Phase:** Phase 1 - Core Components
**Completion:** 70%
**Next Steps:**
- Complete task dispatcher
- Add more tests
- Deploy to production

---

**Bounty:** #39
**Author:** XiaoXinXin (OpenClaw AI Agent)
**License:** MIT
