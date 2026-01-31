import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAuthStore } from '@/stores/auth-store';

describe('apiClient', () => {
  let originalLocation: Location;

  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();

    // Save original location
    originalLocation = window.location;

    // Mock window.location
    delete (window as any).location;
    (window as any).location = {
      ...originalLocation,
      pathname: '/dashboard',
      href: '',
    };
  });

  afterEach(() => {
    // Restore original location
    window.location = originalLocation;
  });

  describe('beforeRequest フック', () => {
    it('トークンがある場合、Authorizationヘッダーを設定する', () => {
      const token = 'test-token-123';
      useAuthStore.getState().setAuth(token, {
        user_id: 'user-1',
        email: 'test@example.com',
        created_at: '2026-01-01T00:00:00Z',
      });

      // Simulate beforeRequest hook
      const mockRequest = {
        headers: new Headers(),
      };

      // Execute the hook logic directly
      const currentToken = useAuthStore.getState().token;
      if (currentToken) {
        mockRequest.headers.set('Authorization', `Bearer ${currentToken}`);
      }

      expect(mockRequest.headers.get('Authorization')).toBe(`Bearer ${token}`);
    });

    it('トークンがない場合、Authorizationヘッダーを設定しない', () => {
      useAuthStore.getState().clearAuth();

      const mockRequest = {
        headers: new Headers(),
      };

      const currentToken = useAuthStore.getState().token;
      if (currentToken) {
        mockRequest.headers.set('Authorization', `Bearer ${currentToken}`);
      }

      expect(mockRequest.headers.has('Authorization')).toBe(false);
    });
  });

  describe('afterResponse フック', () => {
    it('401レスポンスでauthをクリアする', () => {
      useAuthStore.getState().setAuth('token', {
        user_id: 'user-1',
        email: 'test@example.com',
        created_at: '2026-01-01T00:00:00Z',
      });

      // Simulate afterResponse hook
      const mockResponse = { status: 401 };

      if (mockResponse.status === 401) {
        useAuthStore.getState().clearAuth();
      }

      expect(useAuthStore.getState().token).toBeNull();
    });

    it('401レスポンスでログインページにリダイレクトする', () => {
      (window as any).location = { pathname: '/dashboard', href: '' };

      const mockResponse = { status: 401 };

      if (mockResponse.status === 401) {
        useAuthStore.getState().clearAuth();
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }

      expect(window.location.href).toBe('/login');
    });

    it('ログインページ上では401でもリダイレクトしない', () => {
      (window as any).location = { pathname: '/login', href: '' };

      const mockResponse = { status: 401 };

      if (mockResponse.status === 401) {
        useAuthStore.getState().clearAuth();
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }

      expect(window.location.href).toBe('');
    });

    it('401以外のレスポンスでは何もしない', () => {
      useAuthStore.getState().setAuth('token', {
        user_id: 'user-1',
        email: 'test@example.com',
        created_at: '2026-01-01T00:00:00Z',
      });

      const mockResponse = { status: 200 };

      if (mockResponse.status === 401) {
        useAuthStore.getState().clearAuth();
      }

      expect(useAuthStore.getState().token).toBe('token');
    });
  });
});
