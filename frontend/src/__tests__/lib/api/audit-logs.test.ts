import { describe, it, expect, vi, beforeEach } from 'vitest';
import { auditLogsApi } from '@/lib/api/audit-logs';
import type { PaginatedResponse, AuditLog } from '@/types';

// Mock apiClient
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';
const mockGet = apiClient.get as ReturnType<typeof vi.fn>;

describe('auditLogsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('パラメータなしでGETリクエストを送信する', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      const result = await auditLogsApi.list();

      expect(mockGet).toHaveBeenCalledWith('audit-logs', { searchParams: expect.any(URLSearchParams) });
      expect(result).toEqual(mockResponse);
    });

    it('event_typeパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({ event_type: 'USER_LOGIN' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('event_type')).toBe('USER_LOGIN');
    });

    it('user_idパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({ user_id: 'user-001' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('user_id')).toBe('user-001');
    });

    it('target_idパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({ target_id: 'dashboard-001' });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('target_id')).toBe('dashboard-001');
    });

    it('start_dateとend_dateパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({
        start_date: '2026-02-01T00:00:00Z',
        end_date: '2026-02-06T23:59:59Z',
      });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('start_date')).toBe('2026-02-01T00:00:00Z');
      expect(searchParams.get('end_date')).toBe('2026-02-06T23:59:59Z');
    });

    it('limit/offsetパラメータを渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 100,
        offset: 50,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({ limit: 100, offset: 50 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('100');
      expect(searchParams.get('offset')).toBe('50');
    });

    it('offset=0でもパラメータが送信される', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 50,
        offset: 0,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({ limit: 50, offset: 0 });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('limit')).toBe('50');
      expect(searchParams.get('offset')).toBe('0');
    });

    it('複数のパラメータを同時に渡す', async () => {
      const mockResponse: PaginatedResponse<AuditLog> = {
        items: [],
        total: 0,
        limit: 20,
        offset: 10,
      };

      mockGet.mockReturnValue({
        json: vi.fn().mockResolvedValue(mockResponse),
      });

      await auditLogsApi.list({
        event_type: 'DASHBOARD_SHARE_ADDED',
        user_id: 'user-001',
        limit: 20,
        offset: 10,
      });

      const call = mockGet.mock.calls[0];
      const searchParams = call[1].searchParams as URLSearchParams;
      expect(searchParams.get('event_type')).toBe('DASHBOARD_SHARE_ADDED');
      expect(searchParams.get('user_id')).toBe('user-001');
      expect(searchParams.get('limit')).toBe('20');
      expect(searchParams.get('offset')).toBe('10');
    });
  });
});
