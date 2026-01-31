import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useLogin, useLogout, useCurrentUser } from '@/hooks/use-auth';
import { useAuthStore } from '@/stores/auth-store';
import { createWrapper, createMockUser } from '@/__tests__/helpers/test-utils';
import type { LoginRequest, LoginResponse, UserWithGroups } from '@/types';

// Mock authApi
vi.mock('@/lib/api', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}));

import { authApi } from '@/lib/api';
const mockLogin = authApi.login as ReturnType<typeof vi.fn>;
const mockLogout = authApi.logout as ReturnType<typeof vi.fn>;
const mockMe = authApi.me as ReturnType<typeof vi.fn>;

describe('useLogin', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();
  });

  it('ログイン成功時にsetAuthを呼びクエリを無効化する', async () => {
    const loginRequest: LoginRequest = {
      email: 'test@example.com',
      password: 'password123',
    };

    const mockResponse: LoginResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: createMockUser({ email: 'test@example.com' }),
    };

    mockLogin.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });

    result.current.mutate(loginRequest);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockLogin).toHaveBeenCalledWith(loginRequest);
    expect(useAuthStore.getState().token).toBe('test-token');
    expect(useAuthStore.getState().user).toEqual(mockResponse.user);
  });

  it('ログインリクエストを送信する', async () => {
    const loginRequest: LoginRequest = {
      email: 'test@example.com',
      password: 'password123',
    };

    const mockResponse: LoginResponse = {
      access_token: 'token',
      token_type: 'bearer',
      expires_in: 3600,
      user: createMockUser(),
    };

    mockLogin.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });

    result.current.mutate(loginRequest);

    await waitFor(() => expect(mockLogin).toHaveBeenCalled());
    expect(mockLogin).toHaveBeenCalledWith(loginRequest);
  });
});

describe('useLogout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();
  });

  it('ログアウト成功時にclearAuthを呼びクエリをクリアする', async () => {
    useAuthStore.getState().setAuth('test-token', createMockUser());
    mockLogout.mockResolvedValue(undefined);

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockLogout).toHaveBeenCalled();
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });

  it('ログアウト失敗時もclearAuthを呼ぶ', async () => {
    useAuthStore.getState().setAuth('test-token', createMockUser());
    mockLogout.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useLogout(), { wrapper: createWrapper() });

    result.current.mutate();

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(mockLogout).toHaveBeenCalled();
    expect(useAuthStore.getState().token).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
  });
});

describe('useCurrentUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();
  });

  it('認証済みの場合にユーザー情報を取得する', async () => {
    const mockUser: UserWithGroups = {
      ...createMockUser(),
      groups: [
        { group_id: 'group-1', name: 'Admin' },
      ],
    };

    mockMe.mockResolvedValue(mockUser);
    useAuthStore.getState().setAuth('test-token', createMockUser());

    const { result } = renderHook(() => useCurrentUser(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockMe).toHaveBeenCalled();
    expect(result.current.data).toEqual(mockUser);
  });

  it('未認証の場合はクエリを実行しない', async () => {
    useAuthStore.getState().clearAuth();

    const { result } = renderHook(() => useCurrentUser(), { wrapper: createWrapper() });

    // enabled: false なので実行されない
    expect(result.current.isFetching).toBe(false);
    expect(mockMe).not.toHaveBeenCalled();
  });
});
