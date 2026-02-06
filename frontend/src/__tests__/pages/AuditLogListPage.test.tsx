import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuditLogListPage } from '@/pages/AuditLogListPage';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { AuditLog, PaginatedResponse } from '@/types';

vi.mock('@/hooks', () => ({
  useAuditLogs: vi.fn(),
}));

import { useAuditLogs } from '@/hooks';
const mockUseAuditLogs = useAuditLogs as ReturnType<typeof vi.fn>;

// Helper to create mock audit log
function createMockAuditLog(overrides?: Partial<AuditLog>): AuditLog {
  return {
    log_id: 'log-001',
    timestamp: '2026-02-06T10:00:00Z',
    event_type: 'USER_LOGIN',
    user_id: 'user-001',
    target_type: 'user',
    target_id: 'user-001',
    details: {},
    request_id: 'req-001',
    ...overrides,
  };
}

// Helper to create paginated response
function createMockAuditLogResponse(items: AuditLog[], total = items.length): PaginatedResponse<AuditLog> {
  return {
    data: items,
    pagination: {
      total,
      limit: items.length || 50,
      offset: 0,
      has_next: total > items.length,
    },
  };
}

describe('AuditLogListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseAuditLogs.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('監査ログ一覧をテーブルに表示する', () => {
    const logs = [
      createMockAuditLog({
        log_id: 'log-001',
        event_type: 'USER_LOGIN',
        user_id: 'user-001',
        target_id: 'target-001'
      }),
      createMockAuditLog({
        log_id: 'log-002',
        event_type: 'USER_LOGOUT',
        user_id: 'user-002',
        target_id: 'target-002'
      }),
    ];

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getAllByText('user-001')).toHaveLength(1);
    expect(screen.getAllByText('user-002')).toHaveLength(1);
    expect(screen.getByText('ユーザーログイン')).toBeInTheDocument();
    expect(screen.getByText('ユーザーログアウト')).toBeInTheDocument();
  });

  it('ログがない場合はメッセージを表示する', () => {
    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('監査ログがありません')).toBeInTheDocument();
  });

  it('タイムスタンプが日本語形式で表示される', () => {
    const logs = [
      createMockAuditLog({ timestamp: '2026-02-06T10:30:45Z' }),
    ];

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    // タイムスタンプが表示されていることを確認
    const timestamp = screen.getByText(/2026/);
    expect(timestamp).toBeInTheDocument();
  });

  it('イベントタイプがバッジで表示される', () => {
    const logs = [
      createMockAuditLog({ event_type: 'DASHBOARD_SHARE_ADDED' }),
    ];

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('ダッシュボード共有追加')).toBeInTheDocument();
  });

  it('イベントタイプフィルターのセレクトボックスが表示される', () => {
    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('ページネーションが表示される', () => {
    const logs = Array.from({ length: 50 }, (_, i) =>
      createMockAuditLog({ log_id: `log-${i}` })
    );

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs, 200),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText(/200件中/)).toBeInTheDocument();
  });

  it('各種イベントタイプが正しく表示される', () => {
    const logs = [
      createMockAuditLog({ log_id: 'log-001', event_type: 'USER_LOGIN' }),
      createMockAuditLog({ log_id: 'log-002', event_type: 'USER_LOGOUT' }),
      createMockAuditLog({ log_id: 'log-003', event_type: 'USER_LOGIN_FAILED' }),
      createMockAuditLog({ log_id: 'log-004', event_type: 'DATASET_CREATED' }),
      createMockAuditLog({ log_id: 'log-005', event_type: 'TRANSFORM_EXECUTED' }),
    ];

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('ユーザーログイン')).toBeInTheDocument();
    expect(screen.getByText('ユーザーログアウト')).toBeInTheDocument();
    expect(screen.getByText('ログイン失敗')).toBeInTheDocument();
    expect(screen.getByText('データセット作成')).toBeInTheDocument();
    expect(screen.getByText('Transform実行')).toBeInTheDocument();
  });

  it('target_typeとtarget_idが表示される', () => {
    const logs = [
      createMockAuditLog({
        target_type: 'dashboard',
        target_id: 'dashboard-001',
      }),
    ];

    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse(logs),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('dashboard')).toBeInTheDocument();
    expect(screen.getByText('dashboard-001')).toBeInTheDocument();
  });

  it('テーブルヘッダーが正しく表示される', () => {
    mockUseAuditLogs.mockReturnValue({
      data: createMockAuditLogResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><AuditLogListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('タイムスタンプ')).toBeInTheDocument();
    expect(screen.getByText('イベントタイプ')).toBeInTheDocument();
    expect(screen.getByText('ユーザーID')).toBeInTheDocument();
    expect(screen.getByText('対象タイプ')).toBeInTheDocument();
    expect(screen.getByText('対象ID')).toBeInTheDocument();
  });
});
