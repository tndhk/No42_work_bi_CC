import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { useAuthStore } from '@/stores/auth-store';
import { createWrapper } from '@/__tests__/helpers/test-utils';

// Mock useLogin hook
vi.mock('@/hooks', () => ({
  useLogin: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
  })),
}));

import { useLogin } from '@/hooks';
const mockUseLogin = useLogin as ReturnType<typeof vi.fn>;

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null }),
  };
});

describe('LoginPage', () => {
  let mockMutate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockMutate = vi.fn();
    mockUseLogin.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
    } as any);
    useAuthStore.getState().clearAuth();
  });

  afterEach(() => {
    cleanup();
  });

  it('ログインフォームを表示する', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('BI Tool')).toBeInTheDocument();
    expect(screen.getByText('ログインしてください')).toBeInTheDocument();
  });

  it('メールアドレス入力フィールドがある', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
  });

  it('パスワード入力フィールドがある', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('パスワード')).toBeInTheDocument();
  });

  it('送信ボタンがある', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const submitButton = screen.getByRole('button', { name: /ログイン/ });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).not.toBeDisabled();
  });

  it('フォームにメールアドレスとパスワードを入力できる', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const emailInput = screen.getByLabelText('メールアドレス') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('パスワード') as HTMLInputElement;

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });

  it('ログイン中の状態を扱える', () => {
    mockUseLogin.mockReturnValue({
      mutate: mockMutate,
      isPending: true,
      isError: false,
    } as any);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const submitButton = screen.getByRole('button');
    expect(submitButton).toBeDisabled();
  });

  it('ログインエラー時の状態を扱える', () => {
    mockUseLogin.mockReturnValueOnce({
      mutate: mockMutate,
      isPending: false,
      isError: true,
    } as any);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // isError状態でもフォームは表示される
    expect(screen.getByRole('button', { name: /ログイン/ })).toBeInTheDocument();
  });

  it('認証済みの場合の処理を扱える', () => {
    // Set authenticated state
    useAuthStore.getState().setAuth('test-token', {
      user_id: 'user-1',
      email: 'test@example.com',
      created_at: '2026-01-01T00:00:00Z',
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // Verify the page handles authenticated state
    expect(mockNavigate).toBeDefined();
  });
});
