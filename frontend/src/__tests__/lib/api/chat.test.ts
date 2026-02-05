import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ChatRequest, ChatSource } from '@/types';

// Mock useAuthStore
vi.mock('@/stores/auth-store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ token: 'test-token-abc' })),
  },
}));

// We need to import after mocks are set up
import { sendChatMessage } from '@/lib/api/chat';
import { useAuthStore } from '@/stores/auth-store';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Encode a string as a Uint8Array (UTF-8). */
function encode(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

/**
 * Build a ReadableStream that yields the given chunks sequentially.
 * Each chunk is a string that will be encoded to Uint8Array.
 */
function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  let index = 0;
  return new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encode(chunks[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

/** Build a minimal Response with a body stream from the given chunks. */
function makeSSEResponse(chunks: string[], status = 200): Response {
  return new Response(makeStream(chunks), {
    status,
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

/** A standard ChatRequest fixture. */
const chatRequest: ChatRequest = {
  message: 'Hello',
  conversation_history: [],
};

const dashboardId = 'dash-123';

describe('sendChatMessage', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    vi.stubGlobal('import', { meta: { env: { VITE_API_URL: 'http://localhost:8000/api' } } });
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      token: 'test-token-abc',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  // -------------------------------------------------------------------------
  // 1. Basic fetch call
  // -------------------------------------------------------------------------
  describe('fetch request construction', () => {
    it('sends POST to correct URL with Bearer token and JSON body', async () => {
      const sseData = 'data: {"type":"done"}\n\n';
      fetchSpy.mockResolvedValue(makeSSEResponse([sseData]));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, options] = fetchSpy.mock.calls[0];

      // URL should contain the dashboardId
      expect(url).toContain(`/dashboards/${dashboardId}/chat`);

      // Method
      expect(options.method).toBe('POST');

      // Headers
      expect(options.headers['Authorization']).toBe('Bearer test-token-abc');
      expect(options.headers['Content-Type']).toBe('application/json');

      // Body
      const body = JSON.parse(options.body);
      expect(body).toEqual(chatRequest);
    });

    it('passes AbortSignal to fetch when provided', async () => {
      const sseData = 'data: {"type":"done"}\n\n';
      fetchSpy.mockResolvedValue(makeSSEResponse([sseData]));

      const controller = new AbortController();
      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks, controller.signal);

      const [, options] = fetchSpy.mock.calls[0];
      expect(options.signal).toBe(controller.signal);
    });
  });

  // -------------------------------------------------------------------------
  // 2. SSE token events
  // -------------------------------------------------------------------------
  describe('SSE token event parsing', () => {
    it('calls onToken for each token event', async () => {
      const chunks = [
        'data: {"type":"token","data":"Hello"}\n\n',
        'data: {"type":"token","data":" World"}\n\n',
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onToken).toHaveBeenCalledTimes(2);
      expect(callbacks.onToken).toHaveBeenNthCalledWith(1, 'Hello');
      expect(callbacks.onToken).toHaveBeenNthCalledWith(2, ' World');
    });

    it('handles multiple SSE events in a single chunk (buffering)', async () => {
      // Two events arrive in the same chunk
      const chunks = [
        'data: {"type":"token","data":"A"}\n\ndata: {"type":"token","data":"B"}\n\n',
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onToken).toHaveBeenCalledTimes(2);
      expect(callbacks.onToken).toHaveBeenNthCalledWith(1, 'A');
      expect(callbacks.onToken).toHaveBeenNthCalledWith(2, 'B');
    });

    it('handles SSE events split across chunks (partial buffering)', async () => {
      // An event is split across two chunks
      const chunks = [
        'data: {"type":"tok',
        'en","data":"split"}\n\ndata: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onToken).toHaveBeenCalledTimes(1);
      expect(callbacks.onToken).toHaveBeenCalledWith('split');
    });
  });

  // -------------------------------------------------------------------------
  // 3. SSE done events
  // -------------------------------------------------------------------------
  describe('SSE done event parsing', () => {
    it('calls onDone with sources when done event has sources', async () => {
      const sources: ChatSource[] = [
        { dataset_name: 'sales', relevance: 'high' },
        { dataset_name: 'inventory', relevance: 'medium' },
      ];
      const chunks = [
        'data: {"type":"token","data":"Answer"}\n\n',
        `data: {"type":"done","sources":${JSON.stringify(sources)}}\n\n`,
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onDone).toHaveBeenCalledTimes(1);
      expect(callbacks.onDone).toHaveBeenCalledWith(sources);
    });

    it('calls onDone with empty array when done event has no sources', async () => {
      const chunks = [
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onDone).toHaveBeenCalledTimes(1);
      expect(callbacks.onDone).toHaveBeenCalledWith([]);
    });
  });

  // -------------------------------------------------------------------------
  // 4. SSE error events
  // -------------------------------------------------------------------------
  describe('SSE error event parsing', () => {
    it('calls onError when server sends an error event', async () => {
      const chunks = [
        'data: {"type":"error","error":"Something went wrong"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onError).toHaveBeenCalledTimes(1);
      expect(callbacks.onError).toHaveBeenCalledWith('Something went wrong');
      expect(callbacks.onToken).not.toHaveBeenCalled();
      expect(callbacks.onDone).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // 5. HTTP error responses
  // -------------------------------------------------------------------------
  describe('HTTP error handling', () => {
    it('calls onError when response status is not ok', async () => {
      const errorBody = JSON.stringify({ detail: 'Unauthorized' });
      fetchSpy.mockResolvedValue(
        new Response(errorBody, {
          status: 401,
          statusText: 'Unauthorized',
          headers: { 'Content-Type': 'application/json' },
        })
      );

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onError).toHaveBeenCalledTimes(1);
      // Error message should contain the status or detail
      expect(callbacks.onError.mock.calls[0][0]).toContain('401');
    });

    it('calls onError when fetch throws a network error', async () => {
      fetchSpy.mockRejectedValue(new TypeError('Failed to fetch'));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onError).toHaveBeenCalledTimes(1);
      expect(callbacks.onError.mock.calls[0][0]).toContain('Failed to fetch');
    });

    it('calls onError when response body is null', async () => {
      fetchSpy.mockResolvedValue(
        new Response(null, {
          status: 200,
          headers: { 'Content-Type': 'text/event-stream' },
        })
      );

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onError).toHaveBeenCalledTimes(1);
      expect(callbacks.onError.mock.calls[0][0]).toBeTruthy();
    });
  });

  // -------------------------------------------------------------------------
  // 6. Abort handling
  // -------------------------------------------------------------------------
  describe('abort handling', () => {
    it('does not call onError when aborted (AbortError)', async () => {
      const abortError = new DOMException('The operation was aborted', 'AbortError');
      fetchSpy.mockRejectedValue(abortError);

      const controller = new AbortController();
      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks, controller.signal);

      // AbortError should be silently ignored, not trigger onError
      expect(callbacks.onError).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // 7. Auth token missing
  // -------------------------------------------------------------------------
  describe('auth token handling', () => {
    it('sends request without Authorization header when token is null', async () => {
      (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
        token: null,
      });

      const chunks = ['data: {"type":"done"}\n\n'];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      const [, options] = fetchSpy.mock.calls[0];
      expect(options.headers['Authorization']).toBeUndefined();
    });
  });

  // -------------------------------------------------------------------------
  // 8. Edge cases: malformed SSE data
  // -------------------------------------------------------------------------
  describe('edge cases', () => {
    it('ignores SSE lines that are not data lines (e.g., comments, event:)', async () => {
      const chunks = [
        ': this is a comment\n\n',
        'event: message\ndata: {"type":"token","data":"ok"}\n\n',
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      expect(callbacks.onToken).toHaveBeenCalledWith('ok');
      expect(callbacks.onDone).toHaveBeenCalled();
    });

    it('skips events with invalid JSON gracefully', async () => {
      const chunks = [
        'data: {invalid json}\n\n',
        'data: {"type":"token","data":"valid"}\n\n',
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      // Should continue processing despite the invalid JSON
      expect(callbacks.onToken).toHaveBeenCalledWith('valid');
      expect(callbacks.onDone).toHaveBeenCalled();
    });

    it('handles empty data lines', async () => {
      const chunks = [
        'data: \n\n',
        'data: {"type":"done"}\n\n',
      ];
      fetchSpy.mockResolvedValue(makeSSEResponse(chunks));

      const callbacks = {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: vi.fn(),
      };

      await sendChatMessage(dashboardId, chatRequest, callbacks);

      // Should not crash, and done should still fire
      expect(callbacks.onDone).toHaveBeenCalled();
    });
  });
});
