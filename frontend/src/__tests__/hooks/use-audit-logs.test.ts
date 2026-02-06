import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAuditLogs } from '@/hooks/use-audit-logs';
import { createWrapper, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';
import type { AuditLog } from '@/types';

// Mock auditLogsApi
vi.mock('@/lib/api', () => ({
  auditLogsApi: {
    list: vi.fn(),
  },
}));

import { auditLogsApi } from '@/lib/api';
const mockList = auditLogsApi.list as ReturnType<typeof vi.fn>;

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

describe('useAuditLogs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('監査ログ一覧を取得する', async () => {
    const mockLogs = [
      createMockAuditLog(),
      createMockAuditLog({ log_id: 'log-002', event_type: 'USER_LOGOUT' }),
    ];
    const mockResponse = createMockPaginatedResponse(mockLogs);

    mockList.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuditLogs(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(undefined);
    expect(result.current.data).toEqual(mockResponse);
  });

  it('パラメータ付きでログを取得する', async () => {
    const params = {
      event_type: 'USER_LOGIN' as const,
      user_id: 'user-001',
      limit: 20,
      offset: 10,
    };
    const mockLogs = [createMockAuditLog()];
    const mockResponse = createMockPaginatedResponse(mockLogs);

    mockList.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuditLogs(params), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockList).toHaveBeenCalledWith(params);
    expect(result.current.data).toEqual(mockResponse);
  });

  it('event_typeフィルターが正しく渡される', async () => {
    const params = { event_type: 'DASHBOARD_SHARE_ADDED' as const };
    const mockResponse = createMockPaginatedResponse([]);

    mockList.mockResolvedValue(mockResponse);

    renderHook(() => useAuditLogs(params), { wrapper: createWrapper() });

    await waitFor(() => expect(mockList).toHaveBeenCalled());

    expect(mockList).toHaveBeenCalledWith(params);
  });

  it('日付範囲フィルターが正しく渡される', async () => {
    const params = {
      start_date: '2026-02-01T00:00:00Z',
      end_date: '2026-02-06T23:59:59Z',
    };
    const mockResponse = createMockPaginatedResponse([]);

    mockList.mockResolvedValue(mockResponse);

    renderHook(() => useAuditLogs(params), { wrapper: createWrapper() });

    await waitFor(() => expect(mockList).toHaveBeenCalled());

    expect(mockList).toHaveBeenCalledWith(params);
  });

  it('target_idフィルターが正しく渡される', async () => {
    const params = { target_id: 'dashboard-001' };
    const mockResponse = createMockPaginatedResponse([]);

    mockList.mockResolvedValue(mockResponse);

    renderHook(() => useAuditLogs(params), { wrapper: createWrapper() });

    await waitFor(() => expect(mockList).toHaveBeenCalled());

    expect(mockList).toHaveBeenCalledWith(params);
  });
});
