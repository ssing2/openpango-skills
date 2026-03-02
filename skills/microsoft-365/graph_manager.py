#!/usr/bin/env python3
"""
Microsoft 365 Graph manager for OpenPango.

Implements:
- send_teams_message(channel, content)
- read_outlook_inbox()
- read_excel_range(file_id, range)

Supports both application-level and delegated permissions via MSAL.
Runs in mock mode when credentials or MSAL are unavailable.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import msal  # type: ignore
except Exception:  # pragma: no cover
    msal = None


logger = logging.getLogger("M365GraphManager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPE = ["https://graph.microsoft.com/.default"]


@dataclass
class GraphConfig:
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    auth_mode: str = "application"  # application | delegated
    mailbox_user: str = ""  # required for app-only mailbox/drive operations


class GraphManager:
    def __init__(self, credential_store_path: Optional[str] = None, timeout_seconds: int = 20):
        self.timeout_seconds = timeout_seconds
        self.credential_store_path = Path(
            credential_store_path
            or os.getenv("OPENPANGO_AGENT_INTEGRATIONS_PATH", "~/.openpango/agent_integrations.json")
        ).expanduser()

        self._integrations = self._load_agent_integrations()
        self.config = self._build_config()
        self._msal_app = None

        self.mock_mode = not self._has_minimum_config()
        if self.mock_mode:
            logger.warning("M365 Graph manager in MOCK mode (missing config or msal package)")

    # --------------------------
    # Public tools (required)
    # --------------------------

    def send_teams_message(self, channel: str, content: str) -> Dict[str, Any]:
        """
        Send a message to Microsoft Teams.

        `channel` supports:
        - "team_id/channel_id"
        - "teams/{team_id}/channels/{channel_id}"
        """
        team_id, channel_id = self._parse_channel(channel)
        endpoint = f"/teams/{team_id}/channels/{channel_id}/messages"
        payload = {"body": {"content": content}}
        return self._graph_request("POST", endpoint, payload=payload)

    def read_outlook_inbox(self, limit: int = 10) -> Dict[str, Any]:
        """Read inbox messages with pagination support."""
        root = self._mailbox_root()
        params = {
            "$top": str(max(1, min(limit, 50))),
            "$orderby": "receivedDateTime DESC",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
        }

        data = self._graph_request("GET", f"{root}/messages", params=params)
        items = list(data.get("value", []))

        next_link = data.get("@odata.nextLink")
        while next_link and len(items) < limit:
            page = self._graph_request("GET", next_link)
            items.extend(page.get("value", []))
            next_link = page.get("@odata.nextLink")

        return {
            "messages": items[:limit],
            "count": min(len(items), limit),
            "auth_mode": self.config.auth_mode,
        }

    def read_excel_range(self, file_id: str, range: str, worksheet: str = "Sheet1") -> Dict[str, Any]:
        """Read an Excel range from OneDrive/SharePoint-backed file via Graph."""
        root = self._mailbox_root()
        ws = urllib.parse.quote(worksheet)
        addr = urllib.parse.quote(range)
        endpoint = f"{root}/drive/items/{file_id}/workbook/worksheets('{ws}')/range(address='{addr}')"
        return self._graph_request("GET", endpoint)

    # --------------------------
    # Credential & auth handling
    # --------------------------

    def set_delegated_refresh_token(self, refresh_token: str) -> None:
        """Persist delegated refresh token in agent_integrations-like store."""
        key = "m365"
        if key not in self._integrations:
            self._integrations[key] = {}
        self._integrations[key]["refresh_token"] = refresh_token
        self._persist_agent_integrations()

    def _has_minimum_config(self) -> bool:
        if self.config.auth_mode not in ("application", "delegated"):
            return False
        if not self.config.tenant_id or not self.config.client_id:
            return False
        if msal is None:
            return False
        if self.config.auth_mode == "application" and not self.config.client_secret:
            return False
        return True

    def _build_config(self) -> GraphConfig:
        cred = self._integrations.get("m365", {})
        nested_cred = self._integrations.get("agent_integrations", {}).get("m365", {})

        tenant_id = os.getenv("M365_TENANT_ID") or cred.get("tenant_id") or nested_cred.get("tenant_id", "")
        client_id = os.getenv("M365_CLIENT_ID") or cred.get("client_id") or nested_cred.get("client_id", "")
        client_secret = (
            os.getenv("M365_CLIENT_SECRET")
            or cred.get("client_secret")
            or nested_cred.get("client_secret", "")
        )
        auth_mode = (
            os.getenv("M365_AUTH_MODE")
            or cred.get("auth_mode")
            or nested_cred.get("auth_mode")
            or "application"
        ).lower()
        mailbox_user = (
            os.getenv("M365_MAILBOX_USER")
            or cred.get("mailbox_user")
            or nested_cred.get("mailbox_user", "")
        )

        return GraphConfig(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            auth_mode=auth_mode,
            mailbox_user=mailbox_user,
        )

    def _authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.config.tenant_id}"

    def _get_msal_client(self):
        if self._msal_app is not None:
            return self._msal_app

        if self.config.auth_mode == "application":
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=self.config.client_secret,
                authority=self._authority(),
            )
        else:
            self._msal_app = msal.PublicClientApplication(
                client_id=self.config.client_id,
                authority=self._authority(),
            )
        return self._msal_app

    def _get_access_token(self) -> str:
        if self.mock_mode:
            return "mock-token"

        client = self._get_msal_client()

        if self.config.auth_mode == "application":
            token = client.acquire_token_silent(DEFAULT_SCOPE, account=None)
            if not token:
                token = client.acquire_token_for_client(scopes=DEFAULT_SCOPE)
            if "access_token" not in token:
                raise RuntimeError(f"MSAL app auth failed: {token}")
            return token["access_token"]

        # delegated mode
        accounts = client.get_accounts()
        token = None
        if accounts:
            token = client.acquire_token_silent(DEFAULT_SCOPE, account=accounts[0])

        refresh_token = (
            self._integrations.get("m365", {}).get("refresh_token")
            or self._integrations.get("agent_integrations", {}).get("m365", {}).get("refresh_token")
            or ""
        )
        if not token and refresh_token and hasattr(client, "acquire_token_by_refresh_token"):
            token = client.acquire_token_by_refresh_token(refresh_token, DEFAULT_SCOPE)

        if not token and os.getenv("M365_ALLOW_DEVICE_CODE", "0") == "1":
            flow = client.initiate_device_flow(scopes=DEFAULT_SCOPE)
            if "user_code" not in flow:
                raise RuntimeError(f"Device code flow init failed: {flow}")
            logger.info("Complete delegated login with code: %s", flow.get("user_code"))
            token = client.acquire_token_by_device_flow(flow)

        if not token or "access_token" not in token:
            raise RuntimeError(
                "MSAL delegated auth failed. Provide refresh token or set M365_ALLOW_DEVICE_CODE=1 for interactive flow."
            )
        return token["access_token"]

    # --------------------------
    # Graph API helpers
    # --------------------------

    def _mailbox_root(self) -> str:
        if self.config.auth_mode == "application" and self.config.mailbox_user:
            return f"/users/{self.config.mailbox_user}"
        return "/me"

    def _graph_request(
        self,
        method: str,
        path_or_url: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        retries: int = 3,
    ) -> Dict[str, Any]:
        if self.mock_mode:
            return {
                "mocked": True,
                "method": method,
                "path": path_or_url,
                "payload": payload or {},
                "params": params or {},
                "value": [],
            }

        token = self._get_access_token()

        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{GRAPH_BASE_URL}{path_or_url}"

        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}{'&' if '?' in url else '?'}{query}"

        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        attempt = 0
        while True:
            req = urllib.request.Request(url=url, data=body, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 503) and attempt < retries:
                    retry_after = int(exc.headers.get("Retry-After", "1"))
                    time.sleep(max(1, retry_after))
                    attempt += 1
                    continue
                detail = exc.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"Graph API error {exc.code}: {detail}") from exc
            except urllib.error.URLError as exc:
                if attempt < retries:
                    time.sleep(2**attempt)
                    attempt += 1
                    continue
                raise RuntimeError(f"Graph API network error: {exc}") from exc

    @staticmethod
    def _parse_channel(channel: str) -> Tuple[str, str]:
        val = channel.strip().strip("/")

        if val.startswith("teams/"):
            # teams/{team_id}/channels/{channel_id}
            parts = val.split("/")
            if len(parts) >= 4 and parts[0] == "teams" and parts[2] == "channels":
                return parts[1], parts[3]

        # fallback: team_id/channel_id
        parts = val.split("/")
        if len(parts) == 2 and all(parts):
            return parts[0], parts[1]

        raise ValueError(
            "Invalid channel format. Use 'team_id/channel_id' or 'teams/{team_id}/channels/{channel_id}'."
        )

    # --------------------------
    # Agent integrations store
    # --------------------------

    def _load_agent_integrations(self) -> Dict[str, Any]:
        env_path = os.getenv("OPENPANGO_AGENT_CREDENTIALS_PATH")
        if env_path:
            p = Path(env_path).expanduser()
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    logger.warning("Failed to parse OPENPANGO_AGENT_CREDENTIALS_PATH JSON: %s", p)

        if self.credential_store_path.exists():
            try:
                return json.loads(self.credential_store_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Failed to parse credential store: %s", self.credential_store_path)

        return {}

    def _persist_agent_integrations(self) -> None:
        self.credential_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.credential_store_path.write_text(json.dumps(self._integrations, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # Minimal manual smoke usage
    gm = GraphManager()
    print(json.dumps(gm.read_outlook_inbox(limit=3), indent=2))
