import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Header } from '@/components/common/Header';
import { useAuthStore } from '@/stores/auth-store';
import { createWrapper, createMockUser } from '@/__tests__/helpers/test-utils';

// Mock useLogout hook
vi.mock('@/hooks', () => ({
  useLogout: vi.fn(() => ({
    mutate: vi.fn(),
    isLoading: false,
  })),
}));

import { useLogout } from '@/hooks';
const mockUseLogout = useLogout as ReturnType<typeof vi.fn>;

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.getState().clearAuth();
  });

  afterEach(() => {
    cleanup();
  });

  it('ヘッダーが表示される', () => {
    render(<Header />, { wrapper: createWrapper() });
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('ユーザーがいる場合にメールアドレスを表示する', () => {
    const user = createMockUser({ email: 'test@example.com' });
    useAuthStore.getState().setAuth('test-token', user);

    render(<Header />, { wrapper: createWrapper() });

    // Button内のemailを探す
    expect(screen.getAllByText('test@example.com')[0]).toBeInTheDocument();
  });

  it('ユーザーがいない場合はドロップダウンが表示されない', () => {
    useAuthStore.getState().clearAuth();

    render(<Header />, { wrapper: createWrapper() });

    // ユーザーアイコンボタンが存在しない
    expect(screen.queryByRole('button', { name: /test@example.com/ })).not.toBeInTheDocument();
  });

  it('ログアウトメニュー項目を表示する', async () => {
    const user = userEvent.setup();
    const mockLogout = vi.fn();
    mockUseLogout.mockReturnValue({
      mutate: mockLogout,
      isLoading: false,
    } as any);

    const testUser = createMockUser({ email: 'test@example.com' });
    useAuthStore.getState().setAuth('test-token', testUser);

    render(<Header />, { wrapper: createWrapper() });

    // ドロップダウンメニューを開く
    const trigger = screen.getAllByText('test@example.com')[0].closest('button');
    if (trigger) {
      await user.click(trigger);
    }

    // ログアウトメニュー項目を確認
    const logoutItem = screen.getByText('ログアウト');
    expect(logoutItem).toBeInTheDocument();
  });
});
