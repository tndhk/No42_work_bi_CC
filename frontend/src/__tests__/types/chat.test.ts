import { describe, it, expect, expectTypeOf } from 'vitest';
import type {
  ChatMessage,
  ChatRequest,
  ChatSource,
  ChatTokenEvent,
  ChatDoneEvent,
  ChatErrorEvent,
  ChatSSEEvent,
} from '@/types';
import {
  isChatMessage,
  isChatSource,
  isChatTokenEvent,
  isChatDoneEvent,
  isChatErrorEvent,
  isChatSSEEvent,
} from '@/types';

// ---------------------------------------------------------------------------
// ChatMessage
// ---------------------------------------------------------------------------
describe('ChatMessage', () => {
  it('accepts valid user message', () => {
    const msg: ChatMessage = { role: 'user', content: 'Hello' };
    expect(msg.role).toBe('user');
    expect(msg.content).toBe('Hello');
  });

  it('accepts valid assistant message', () => {
    const msg: ChatMessage = { role: 'assistant', content: 'Hi there' };
    expect(msg.role).toBe('assistant');
    expect(msg.content).toBe('Hi there');
  });

  it('type guard returns true for valid message', () => {
    expect(isChatMessage({ role: 'user', content: 'test' })).toBe(true);
    expect(isChatMessage({ role: 'assistant', content: '' })).toBe(true);
  });

  it('type guard returns false for invalid role', () => {
    expect(isChatMessage({ role: 'system', content: 'test' })).toBe(false);
    expect(isChatMessage({ role: 123, content: 'test' })).toBe(false);
  });

  it('type guard returns false for missing fields', () => {
    expect(isChatMessage({ role: 'user' })).toBe(false);
    expect(isChatMessage({ content: 'test' })).toBe(false);
    expect(isChatMessage(null)).toBe(false);
    expect(isChatMessage(undefined)).toBe(false);
    expect(isChatMessage('string')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ChatRequest
// ---------------------------------------------------------------------------
describe('ChatRequest', () => {
  it('accepts valid request with empty history', () => {
    const req: ChatRequest = { message: 'Hello', conversation_history: [] };
    expect(req.message).toBe('Hello');
    expect(req.conversation_history).toHaveLength(0);
  });

  it('accepts valid request with conversation history', () => {
    const req: ChatRequest = {
      message: 'Follow up',
      conversation_history: [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi' },
      ],
    };
    expect(req.conversation_history).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// ChatSource
// ---------------------------------------------------------------------------
describe('ChatSource', () => {
  it('accepts valid source', () => {
    const source: ChatSource = { dataset_name: 'sales_data', relevance: 'high' };
    expect(source.dataset_name).toBe('sales_data');
    expect(source.relevance).toBe('high');
  });

  it('type guard returns true for valid source', () => {
    expect(isChatSource({ dataset_name: 'ds', relevance: 'medium' })).toBe(true);
  });

  it('type guard returns false for invalid source', () => {
    expect(isChatSource({ dataset_name: 'ds' })).toBe(false);
    expect(isChatSource({ relevance: 'high' })).toBe(false);
    expect(isChatSource(null)).toBe(false);
    expect(isChatSource(42)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ChatTokenEvent
// ---------------------------------------------------------------------------
describe('ChatTokenEvent', () => {
  it('accepts valid token event', () => {
    const event: ChatTokenEvent = { type: 'token', data: 'Hello' };
    expect(event.type).toBe('token');
    expect(event.data).toBe('Hello');
  });

  it('type guard returns true for valid token event', () => {
    expect(isChatTokenEvent({ type: 'token', data: 'abc' })).toBe(true);
  });

  it('type guard returns false for wrong type', () => {
    expect(isChatTokenEvent({ type: 'done' })).toBe(false);
    expect(isChatTokenEvent({ type: 'token' })).toBe(false);
    expect(isChatTokenEvent(null)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ChatDoneEvent
// ---------------------------------------------------------------------------
describe('ChatDoneEvent', () => {
  it('accepts done event without sources', () => {
    const event: ChatDoneEvent = { type: 'done' };
    expect(event.type).toBe('done');
    expect(event.sources).toBeUndefined();
  });

  it('accepts done event with sources', () => {
    const event: ChatDoneEvent = {
      type: 'done',
      sources: [{ dataset_name: 'ds1', relevance: 'high' }],
    };
    expect(event.type).toBe('done');
    expect(event.sources).toHaveLength(1);
  });

  it('type guard returns true for valid done event', () => {
    expect(isChatDoneEvent({ type: 'done' })).toBe(true);
    expect(isChatDoneEvent({ type: 'done', sources: [] })).toBe(true);
  });

  it('type guard returns false for wrong type', () => {
    expect(isChatDoneEvent({ type: 'token', data: 'x' })).toBe(false);
    expect(isChatDoneEvent(null)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ChatErrorEvent
// ---------------------------------------------------------------------------
describe('ChatErrorEvent', () => {
  it('accepts valid error event', () => {
    const event: ChatErrorEvent = { type: 'error', error: 'Something went wrong' };
    expect(event.type).toBe('error');
    expect(event.error).toBe('Something went wrong');
  });

  it('type guard returns true for valid error event', () => {
    expect(isChatErrorEvent({ type: 'error', error: 'fail' })).toBe(true);
  });

  it('type guard returns false for wrong type', () => {
    expect(isChatErrorEvent({ type: 'done' })).toBe(false);
    expect(isChatErrorEvent({ type: 'error' })).toBe(false);
    expect(isChatErrorEvent(null)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ChatSSEEvent (Union type)
// ---------------------------------------------------------------------------
describe('ChatSSEEvent', () => {
  it('type guard identifies token event', () => {
    const event: ChatSSEEvent = { type: 'token', data: 'hello' };
    expect(isChatSSEEvent(event)).toBe(true);
    expect(isChatTokenEvent(event)).toBe(true);
  });

  it('type guard identifies done event', () => {
    const event: ChatSSEEvent = { type: 'done' };
    expect(isChatSSEEvent(event)).toBe(true);
    expect(isChatDoneEvent(event)).toBe(true);
  });

  it('type guard identifies error event', () => {
    const event: ChatSSEEvent = { type: 'error', error: 'oops' };
    expect(isChatSSEEvent(event)).toBe(true);
    expect(isChatErrorEvent(event)).toBe(true);
  });

  it('type guard returns false for unknown event type', () => {
    expect(isChatSSEEvent({ type: 'unknown' })).toBe(false);
    expect(isChatSSEEvent(null)).toBe(false);
    expect(isChatSSEEvent({})).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Compile-time type structure checks (using expectTypeOf)
// ---------------------------------------------------------------------------
describe('Type structure verification', () => {
  it('ChatMessage has correct shape', () => {
    expectTypeOf<ChatMessage>().toHaveProperty('role');
    expectTypeOf<ChatMessage>().toHaveProperty('content');
  });

  it('ChatRequest has correct shape', () => {
    expectTypeOf<ChatRequest>().toHaveProperty('message');
    expectTypeOf<ChatRequest>().toHaveProperty('conversation_history');
  });

  it('ChatSource has correct shape', () => {
    expectTypeOf<ChatSource>().toHaveProperty('dataset_name');
    expectTypeOf<ChatSource>().toHaveProperty('relevance');
  });

  it('ChatTokenEvent has type "token"', () => {
    expectTypeOf<ChatTokenEvent>().toHaveProperty('type');
    expectTypeOf<ChatTokenEvent>().toHaveProperty('data');
  });

  it('ChatDoneEvent has type "done" and optional sources', () => {
    expectTypeOf<ChatDoneEvent>().toHaveProperty('type');
    expectTypeOf<ChatDoneEvent>().toHaveProperty('sources');
  });

  it('ChatErrorEvent has type "error" and error message', () => {
    expectTypeOf<ChatErrorEvent>().toHaveProperty('type');
    expectTypeOf<ChatErrorEvent>().toHaveProperty('error');
  });

  it('ChatSSEEvent is a union of token, done, and error events', () => {
    // Token event is assignable to ChatSSEEvent
    expectTypeOf<ChatTokenEvent>().toMatchTypeOf<ChatSSEEvent>();
    // Done event is assignable to ChatSSEEvent
    expectTypeOf<ChatDoneEvent>().toMatchTypeOf<ChatSSEEvent>();
    // Error event is assignable to ChatSSEEvent
    expectTypeOf<ChatErrorEvent>().toMatchTypeOf<ChatSSEEvent>();
  });
});
