/**
 * content.ts – Content Script injected into every tab
 *
 * WHY: Only content scripts have direct access to the page DOM. This script
 * receives commands from the background service worker and:
 *   1. Executes the requested DOM operation (highlight / click / readDOM / clearOverlay)
 *   2. Shows a visible "Agent Controlling" banner so the user always knows the
 *      agent is active (privacy / UX requirement from the issue).
 *   3. Returns a structured result back to the background worker.
 *
 * Security note: All selectors are used via querySelectorAll only – no eval,
 * no innerHTML assignment from external data – safe against XSS.
 */

import type { AgentMessage, BridgeMessage } from './background';

// ── Banner / overlay state ────────────────────────────────────────────────────

const BANNER_ID = 'openpango-agent-banner';
const HIGHLIGHT_CLASS = 'openpango-highlight';

/** Inject shared styles once per page load */
function ensureStyles() {
  if (document.getElementById('openpango-styles')) return;
  const style = document.createElement('style');
  style.id = 'openpango-styles';
  style.textContent = `
    #${BANNER_ID} {
      position: fixed;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      z-index: 2147483647;
      background: rgba(220, 38, 38, 0.92);
      color: #fff;
      font-family: monospace;
      font-size: 13px;
      padding: 6px 20px;
      border-radius: 0 0 8px 8px;
      pointer-events: none;
      letter-spacing: 0.05em;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.4);
      transition: opacity 0.3s;
    }
    #${BANNER_ID} .dot {
      width: 8px; height: 8px;
      background: #fff;
      border-radius: 50%;
      animation: op-pulse 1s infinite;
    }
    @keyframes op-pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0.3; }
    }
    .${HIGHLIGHT_CLASS} {
      outline: 3px solid #dc2626 !important;
      outline-offset: 2px !important;
      background-color: rgba(220,38,38,0.08) !important;
      transition: outline 0.2s, background-color 0.2s;
    }
  `;
  document.documentElement.appendChild(style);
}

function showBanner(text = 'Agent Controlling') {
  ensureStyles();
  let banner = document.getElementById(BANNER_ID);
  if (!banner) {
    banner = document.createElement('div');
    banner.id = BANNER_ID;
    banner.innerHTML = `<span class="dot"></span><span class="label">${text}</span>`;
    document.documentElement.appendChild(banner);
  } else {
    const label = banner.querySelector('.label');
    if (label) label.textContent = text;
  }
}

function hideBanner() {
  document.getElementById(BANNER_ID)?.remove();
}

function clearHighlights() {
  document.querySelectorAll(`.${HIGHLIGHT_CLASS}`).forEach((el) => {
    el.classList.remove(HIGHLIGHT_CLASS);
  });
}

// ── DOM operations ────────────────────────────────────────────────────────────

function opHighlight(selector: string): { count: number; error?: string } {
  try {
    const elements = document.querySelectorAll(selector);
    if (elements.length === 0) return { count: 0, error: 'No elements matched selector' };
    elements.forEach((el) => el.classList.add(HIGHLIGHT_CLASS));
    showBanner(`Agent Highlighting: ${selector}`);
    return { count: elements.length };
  } catch (e) {
    return { count: 0, error: String(e) };
  }
}

function opClick(selector: string): { clicked: boolean; error?: string } {
  try {
    const el = document.querySelector<HTMLElement>(selector);
    if (!el) return { clicked: false, error: 'Element not found' };
    showBanner(`Agent Clicking: ${selector}`);
    el.click();
    return { clicked: true };
  } catch (e) {
    return { clicked: false, error: String(e) };
  }
}

function opReadDOM(selector?: string): { html: string; error?: string } {
  try {
    const root = selector ? document.querySelector(selector) : document.body;
    if (!root) return { html: '', error: 'Element not found' };
    showBanner('Agent Reading DOM');
    // Return outerHTML trimmed to 50 KB to avoid oversized messages
    const html = root.outerHTML.slice(0, 50_000);
    return { html };
  } catch (e) {
    return { html: '', error: String(e) };
  }
}

function opClearOverlay(): { cleared: true } {
  clearHighlights();
  hideBanner();
  return { cleared: true };
}

// ── Message listener ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener(
  (message: BridgeMessage, _sender, sendResponse) => {
    if (message.type !== 'AGENT_CMD') return false;

    const cmd = message.data as AgentMessage;
    let result: unknown;

    switch (cmd.action) {
      case 'highlight':
        result = opHighlight(cmd.selector ?? 'body');
        break;
      case 'click':
        result = opClick(cmd.selector ?? 'body');
        break;
      case 'readDOM':
        result = opReadDOM(cmd.selector);
        break;
      case 'clearOverlay':
        result = opClearOverlay();
        break;
      default:
        result = { error: `Unknown action: ${(cmd as AgentMessage).action}` };
    }

    sendResponse(result);
    return true; // keep channel open for async sendResponse
  }
);

// ── Page lifecycle: clear overlays on navigation ──────────────────────────────
// WHY: If the user navigates away the content script is torn down but we want
// a fresh slate on the new page load without leftover highlights.
window.addEventListener('beforeunload', () => {
  clearHighlights();
  hideBanner();
});

// ── Sidebar chat UI (injected into page as shadow-DOM) ───────────────────────
// WHY: Shadow DOM prevents page styles from leaking into our sidebar.

function buildSidebar() {
  if (document.getElementById('openpango-sidebar-host')) return;

  ensureStyles();
  const host = document.createElement('div');
  host.id = 'openpango-sidebar-host';
  Object.assign(host.style, {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    zIndex: '2147483646',
    width: '340px',
    maxHeight: '520px',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: 'monospace',
  });

  const shadow = host.attachShadow({ mode: 'closed' });

  shadow.innerHTML = `
    <style>
      :host { all: initial; }
      #panel {
        background: #0a0a0a;
        border: 1px solid #27272a;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        height: 480px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.6);
        font-family: monospace;
        font-size: 13px;
        color: #e4e4e7;
      }
      #header {
        background: #18181b;
        padding: 10px 14px;
        border-bottom: 1px solid #27272a;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: bold;
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        cursor: pointer;
        user-select: none;
      }
      #status-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #dc2626;
        flex-shrink: 0;
      }
      #status-dot.connected { background: #22c55e; }
      #messages {
        flex: 1;
        overflow-y: auto;
        padding: 10px 12px;
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .msg {
        padding: 6px 10px;
        border-radius: 6px;
        max-width: 90%;
        line-height: 1.4;
        word-break: break-word;
      }
      .msg.user   { background: #1d4ed8; align-self: flex-end; }
      .msg.agent  { background: #27272a; align-self: flex-start; }
      .msg.system { background: #451a03; align-self: center; font-size: 11px; color: #fb923c; }
      #input-row {
        display: flex;
        border-top: 1px solid #27272a;
        padding: 8px;
        gap: 6px;
      }
      #chat-input {
        flex: 1;
        background: #18181b;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        padding: 6px 10px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 13px;
        outline: none;
      }
      #chat-input:focus { border-color: #6366f1; }
      #send-btn {
        background: #6366f1;
        color: #fff;
        border: none;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
        font-family: monospace;
        font-size: 13px;
        font-weight: bold;
      }
      #send-btn:hover { background: #4f46e5; }
    </style>
    <div id="panel">
      <div id="header">
        <span id="status-dot"></span>
        OpenPango Copilot
      </div>
      <div id="messages"></div>
      <div id="input-row">
        <input id="chat-input" type="text" placeholder="Message the agent…" autocomplete="off" />
        <button id="send-btn">Send</button>
      </div>
    </div>
  `;

  const messagesEl = shadow.getElementById('messages')!;
  const inputEl    = shadow.getElementById('chat-input') as HTMLInputElement;
  const sendBtn    = shadow.getElementById('send-btn') as HTMLButtonElement;
  const statusDot  = shadow.getElementById('status-dot') as HTMLElement;
  const header     = shadow.getElementById('header') as HTMLElement;
  let collapsed = false;

  // Toggle collapse on header click
  header.addEventListener('click', () => {
    collapsed = !collapsed;
    const panel = shadow.getElementById('panel') as HTMLElement;
    panel.style.height = collapsed ? '40px' : '480px';
  });

  function appendMessage(text: string, role: 'user' | 'agent' | 'system') {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function sendChat() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = '';
    appendMessage(text, 'user');
    // Send to background → node via runtime message
    chrome.runtime.sendMessage({
      type: 'AGENT_CHAT',
      data: text,
      messageId: `chat-${Date.now()}`,
    } as BridgeMessage);
  }

  sendBtn.addEventListener('click', sendChat);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChat();
  });

  // Listen for agent replies and status updates from background
  chrome.runtime.onMessage.addListener((msg: BridgeMessage) => {
    if (msg.type === 'AGENT_CHAT') {
      appendMessage(String(msg.data), 'agent');
    }
    if (msg.type === 'STATUS') {
      if (msg.data === 'CONNECTED') {
        statusDot.classList.add('connected');
        appendMessage('Connected to OpenPango node', 'system');
      } else {
        statusDot.classList.remove('connected');
        appendMessage('Disconnected – retrying…', 'system');
      }
    }
  });

  // Query initial connection status
  chrome.runtime.sendMessage({ type: 'STATUS', data: null } as BridgeMessage, (status: string) => {
    if (status === 'CONNECTED') statusDot.classList.add('connected');
  });

  document.documentElement.appendChild(host);
}

// Build the sidebar on load; guard against duplicate injection
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', buildSidebar);
} else {
  buildSidebar();
}
