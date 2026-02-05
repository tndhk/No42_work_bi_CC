export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_history: ChatMessage[];
}

export interface ChatSource {
  dataset_name: string;
  relevance: string;
}

export interface ChatTokenEvent {
  type: 'token';
  data: string;
}

export interface ChatDoneEvent {
  type: 'done';
  sources?: ChatSource[];
}

export interface ChatErrorEvent {
  type: 'error';
  error: string;
}

export type ChatSSEEvent = ChatTokenEvent | ChatDoneEvent | ChatErrorEvent;

// ---------------------------------------------------------------------------
// Type Guards
// ---------------------------------------------------------------------------

export function isChatMessage(value: unknown): value is ChatMessage {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    (obj.role === 'user' || obj.role === 'assistant') &&
    typeof obj.content === 'string'
  );
}

export function isChatSource(value: unknown): value is ChatSource {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.dataset_name === 'string' &&
    typeof obj.relevance === 'string'
  );
}

export function isChatTokenEvent(value: unknown): value is ChatTokenEvent {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return obj.type === 'token' && typeof obj.data === 'string';
}

export function isChatDoneEvent(value: unknown): value is ChatDoneEvent {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return obj.type === 'done';
}

export function isChatErrorEvent(value: unknown): value is ChatErrorEvent {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return obj.type === 'error' && typeof obj.error === 'string';
}

export function isChatSSEEvent(value: unknown): value is ChatSSEEvent {
  return isChatTokenEvent(value) || isChatDoneEvent(value) || isChatErrorEvent(value);
}
