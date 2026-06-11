/**
 * WebSocket client with automatic reconnect.
 * Reads messages from the FastAPI /ws endpoint and updates the store.
 */

import {
  posture,
  monitoring,
  settings,
  wsState,
  pushHistory
} from './stores.svelte.js';

let ws: WebSocket | null = null;
let retryTimeout: ReturnType<typeof setTimeout> | null = null;
const RETRY_DELAY_MS = 2000;

export function connect() {
  if (ws && ws.readyState === WebSocket.OPEN) return;

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${protocol}://${window.location.host}/ws`;

  wsState.current = 'connecting';
  ws = new WebSocket(url);

  ws.onopen = () => {
    wsState.current = 'open';
    // Request current state from server
    send({ type: 'get_state' });
  };

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data as string);
      handleMessage(msg);
    } catch {
      // ignore malformed frames
    }
  };

  ws.onerror = () => {
    wsState.current = 'error';
  };

  ws.onclose = () => {
    wsState.current = 'closed';
    ws = null;
    scheduleRetry();
  };
}

export function disconnect() {
  if (retryTimeout) clearTimeout(retryTimeout);
  ws?.close();
  ws = null;
}

export function send(payload: object) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  }
}

function scheduleRetry() {
  if (retryTimeout) clearTimeout(retryTimeout);
  retryTimeout = setTimeout(connect, RETRY_DELAY_MS);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function handleMessage(msg: any) {
  switch (msg.type) {
    case 'posture_update': {
      const entry = {
        status: msg.status,
        confidence: msg.confidence ?? 0,
        issues: msg.issues ?? [],
        message: msg.message ?? '',
        timestamp: msg.timestamp ?? Date.now()
      };
      Object.assign(posture, entry);
      pushHistory(entry);
      break;
    }
    case 'state': {
      monitoring.active = msg.monitoring ?? false;
      if (msg.settings) Object.assign(settings, msg.settings);
      break;
    }
    case 'settings_ack': {
      if (msg.settings) Object.assign(settings, msg.settings);
      break;
    }
  }
}
