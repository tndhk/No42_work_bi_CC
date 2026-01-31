import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '@/stores/auth-store';

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuth();
  });

  it('has initial unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('sets auth with token and user', () => {
    const user = { user_id: 'u1', email: 'a@b.com', created_at: '2024-01-01T00:00:00Z' };
    useAuthStore.getState().setAuth('my-token', user);

    const state = useAuthStore.getState();
    expect(state.token).toBe('my-token');
    expect(state.user).toEqual(user);
    expect(state.isAuthenticated).toBe(true);
  });

  it('clears auth state', () => {
    const user = { user_id: 'u1', email: 'a@b.com', created_at: '2024-01-01T00:00:00Z' };
    useAuthStore.getState().setAuth('my-token', user);
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('does not use localStorage', () => {
    const user = { user_id: 'u1', email: 'a@b.com', created_at: '2024-01-01T00:00:00Z' };
    useAuthStore.getState().setAuth('my-token', user);

    // Verify nothing was stored in localStorage
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('auth')).toBeNull();
  });
});
