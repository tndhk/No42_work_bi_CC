import { useAuthStore } from '@/stores/auth-store';
import type { ChatRequest, ChatSource } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Send a chat message to a dashboard's AI assistant via SSE streaming.
 *
 * Uses raw fetch() instead of ky because ky does not support SSE streaming.
 */
export async function sendChatMessage(
  dashboardId: string,
  request: ChatRequest,
  callbacks: {
    onToken: (token: string) => void;
    onDone: (sources: ChatSource[]) => void;
    onError: (error: string) => void;
  },
  signal?: AbortSignal,
): Promise<void> {
  const token = useAuthStore.getState().token;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/dashboards/${dashboardId}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      signal,
    });
  } catch (err: unknown) {
    // AbortError is silently ignored (user cancelled)
    if (err instanceof DOMException && err.name === 'AbortError') {
      return;
    }
    callbacks.onError(err instanceof Error ? err.message : String(err));
    return;
  }

  if (!response.ok) {
    callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  const body = response.body;
  if (!body) {
    callbacks.onError('Response body is empty');
    return;
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n');
      // The last element may be an incomplete event; keep it in the buffer
      buffer = parts.pop() ?? '';

      for (const part of parts) {
        processSSEEvent(part, callbacks);
      }
    }

    // Process any remaining data in the buffer
    if (buffer.trim()) {
      processSSEEvent(buffer, callbacks);
    }
  } catch (err: unknown) {
    // AbortError during stream read is silently ignored
    if (err instanceof DOMException && err.name === 'AbortError') {
      return;
    }
    callbacks.onError(err instanceof Error ? err.message : String(err));
  }
}

/**
 * Parse and dispatch a single SSE event block.
 */
function processSSEEvent(
  eventBlock: string,
  callbacks: {
    onToken: (token: string) => void;
    onDone: (sources: ChatSource[]) => void;
    onError: (error: string) => void;
  },
): void {
  // Extract the data line(s) from the event block
  const lines = eventBlock.split('\n');
  let dataPayload = '';

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      dataPayload += line.slice(6);
    } else if (line.startsWith('data:')) {
      dataPayload += line.slice(5);
    }
    // Skip comments (lines starting with ':'), event: lines, id: lines, etc.
  }

  if (!dataPayload.trim()) {
    return;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(dataPayload);
  } catch {
    // Skip events with invalid JSON
    return;
  }

  if (typeof parsed !== 'object' || parsed === null) {
    return;
  }

  const event = parsed as Record<string, unknown>;

  switch (event.type) {
    case 'token':
      if (typeof event.data === 'string') {
        callbacks.onToken(event.data);
      }
      break;
    case 'done':
      callbacks.onDone(
        Array.isArray(event.sources) ? (event.sources as ChatSource[]) : [],
      );
      break;
    case 'error':
      if (typeof event.error === 'string') {
        callbacks.onError(event.error);
      }
      break;
  }
}
