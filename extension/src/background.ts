/**
 * background.ts - Service Worker (Manifest V3)
 *
 * WHY: Acts as the central hub. It owns the single WebSocket connection to the
 * local OpenPango node so the connection persists across tab navigations.
 * Content scripts and the sidebar communicate with this worker via chrome.runtime.onMessage.
 *
 * Architecture:
 *   OpenPango Node <--WebSocket--> Background SW <--runtime.sendMessage--> Content Script / Sidebar
 */

// ── Types ────────────────────────────────────────────────────────────────────

export interface AgentMessage {
  action: 'highlight' | 'click' | 'readDOM' | 'clearOverlay' | 'chat';
  selector?: string;       // CSS selector for DOM operations
  payload?: string;        // arbitrary JSON payload / chat text
  messageId?: string;      // round-trip correlation id
}

export interface BridgeMessage {
  type: 'AGENT_CMD' | 'AGENT_CHAT' | 'DOM_RESULT' | 'STATUS' | 'ERROR';
  data: unknown;
  messageId?: string;
}

// ── State ────────────────────────────────────────────────────────────────────

let ws: WebSocket | null = null;
let wsPort: number = 42000;           // default; user can change via popup
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_DELAY_MS = 30_000;
let reconnectAttempts = 0;

// Queue messages that arrive while socket is not yet open
const pendingQueue: string[] = [];

// ── Port management ──────────────────────────────────────────────────────────

/** Restore persisted port from extension storage on startup */
chrome.storage.local.get('openpangoPort', (result) => {
  if (result.openpangoPort) {
    wsPort = Number(result.openpangoPort);
  }
  connectWebSocket();
});

// ── WebSocket lifecycle ───────────────────────────────────────────────────────

function connectWebSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return; // already connected / connecting
  }

  const url = `ws://localhost:${wsPort}`;
  console.log(`[OpenPango] Connecting to ${url}`);

  try {
    ws = new WebSocket(url);
  } catch (err) {
    console.error('[OpenPango] WebSocket construction failed:', err);
    scheduleReconnect();
    return;
  }

  ws.addEventListener('open', () => {
    console.log('[OpenPango] WebSocket connected');
    reconnectAttempts = 0;
    broadcastStatus('CONNECTED');

    // Flush queued messages
    while (pendingQueue.length > 0) {
      ws!.send(pendingQueue.shift()!);
    }
  });

  ws.addEventListener('message', async (event: MessageEvent) => {
    let msg: AgentMessage;
    try {
      msg = JSON.parse(event.data as string) as AgentMessage;
    } catch {
      console.error('[OpenPango] Failed to parse message:', event.data);
      return;
    }

    if (msg.action === 'chat') {
      // Forward chat messages to sidebar
      broadcastToExtension({ type: 'AGENT_CHAT', data: msg.payload, messageId: msg.messageId });
      return;
    }

    // DOM command – route to the active tab's content script
    const tab = await getActiveTab();
    if (!tab?.id) {
      sendToNode({ type: 'ERROR', data: 'No active tab found', messageId: msg.messageId });
      return;
    }

    // Inject content script if needed (handles tabs that loaded before extension install)
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js'],
      });
    } catch {
      // Script already injected – safe to ignore DUPLICATE_SCRIPT errors
    }

    chrome.tabs.sendMessage(tab.id, { type: 'AGENT_CMD', data: msg }, (response) => {
      if (chrome.runtime.lastError) {
        sendToNode({
          type: 'ERROR',
          data: chrome.runtime.lastError.message,
          messageId: msg.messageId,
        });
        return;
      }
      // Echo DOM result back to node
      sendToNode({ type: 'DOM_RESULT', data: response, messageId: msg.messageId });
    });
  });

  ws.addEventListener('close', () => {
    console.log('[OpenPango] WebSocket closed');
    broadcastStatus('DISCONNECTED');
    scheduleReconnect();
  });

  ws.addEventListener('error', (err) => {
    console.error('[OpenPango] WebSocket error', err);
  });
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  const delay = Math.min(RECONNECT_DELAY_MS * 2 ** reconnectAttempts, MAX_RECONNECT_DELAY_MS);
  reconnectAttempts++;
  console.log(`[OpenPango] Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connectWebSocket();
  }, delay);
}

function sendToNode(msg: BridgeMessage) {
  const raw = JSON.stringify(msg);
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(raw);
  } else {
    // Queue so we don't lose responses while reconnecting
    pendingQueue.push(raw);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function getActiveTab(): Promise<chrome.tabs.Tab | undefined> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

/** Broadcast status to all extension views (popup, sidebar) */
function broadcastStatus(status: 'CONNECTED' | 'DISCONNECTED') {
  broadcastToExtension({ type: 'STATUS', data: status });
}

function broadcastToExtension(msg: BridgeMessage) {
  chrome.runtime.sendMessage(msg).catch(() => {
    // No listeners open – safe to ignore
  });
}

// ── Internal message handler (from popup / sidebar) ──────────────────────────

chrome.runtime.onMessage.addListener(
  (message: BridgeMessage & { port?: number; chatText?: string }, _sender, sendResponse) => {
    // Popup requesting status
    if (message.type === 'STATUS') {
      sendResponse(ws?.readyState === WebSocket.OPEN ? 'CONNECTED' : 'DISCONNECTED');
      return true;
    }

    // Popup changing port
    if ((message as { type: string; port?: number }).type === 'SET_PORT') {
      const newPort = (message as { port: number }).port;
      wsPort = newPort;
      chrome.storage.local.set({ openpangoPort: newPort });
      ws?.close(); // triggers reconnect via onclose
      sendResponse('ok');
      return true;
    }

    // Sidebar sending a chat message to the node
    if (message.type === 'AGENT_CHAT') {
      sendToNode(message);
      sendResponse('queued');
      return true;
    }

    return false;
  }
);
