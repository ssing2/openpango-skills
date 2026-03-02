---
name: microsoft-365
description: "Microsoft 365 Graph API integration for Teams, Outlook, and Excel with app/delegated auth modes."
---

# Microsoft 365 Skill

Enterprise integration skill for Microsoft Graph API.

## Tools

- `send_teams_message(channel, content)`
- `read_outlook_inbox(limit=10)`
- `read_excel_range(file_id, range, worksheet="Sheet1")`

## Auth modes

Set `M365_AUTH_MODE`:
- `application` (default) — daemon/service account style
- `delegated` — user delegated permission flow

Required env vars:
- `M365_TENANT_ID`
- `M365_CLIENT_ID`
- `M365_CLIENT_SECRET` (required for application mode)

Optional:
- `M365_MAILBOX_USER` (recommended for application mode)
- `M365_ALLOW_DEVICE_CODE=1` (delegated mode interactive fallback)
- `OPENPANGO_AGENT_CREDENTIALS_PATH` (JSON credentials source)

## Notes

- Uses MSAL when available.
- Falls back to mock mode when configuration is missing.
- Retries throttled requests (HTTP 429/503) using `Retry-After`.
