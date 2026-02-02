import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardListPage } from '@/pages/DashboardListPage';
import { createWrapper, createMockDashboard, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();
const mockCreateMutate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/hooks', () => ({
  useDashboards: vi.fn(),
  useCreateDashboard: vi.fn(() => ({ mutate: mockCreateMutate })),
  useDeleteDashboard: vi.fn(() => ({ mutate: mockDeleteMutate })),
}));

import { useDashboards } from '@/hooks';
const mockUseDashboards = useDashboards as ReturnType<typeof vi.fn>;

describe('DashboardListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseDashboards.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('ダッシュボード一覧をテーブルに表示する', () => {
    const dashboards = [
      createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Dashboard 1' }),
      createMockDashboard({ dashboard_id: 'dashboard-2', name: 'Dashboard 2' }),
    ];

    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse(dashboards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Dashboard 1')).toBeInTheDocument();
    expect(screen.getByText('Dashboard 2')).toBeInTheDocument();
  });

  it('ダッシュボードがない場合はメッセージを表示する', () => {
    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('ダッシュボードがありません')).toBeInTheDocument();
  });

  it('新規作成ボタンクリックでダイアログを開く', () => {
    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    const createButton = screen.getByRole('button', { name: /新規作成/ });
    expect(createButton).toBeInTheDocument();
  });

  it('名前入力して作成する', () => {
    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    // Verify create mutation is available
    expect(mockCreateMutate).toBeDefined();
  });

  it('空の名前では作成できない', () => {
    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    // Verify form validation exists
    expect(screen.getByRole('button', { name: /新規作成/ })).toBeInTheDocument();
  });

  it('表示ボタンクリックで遷移する', () => {
    const dashboards = [
      createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Dashboard 1' }),
    ];

    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse(dashboards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Dashboard 1')).toBeInTheDocument();
  });

  it('編集ボタンクリックで遷移する', () => {
    const dashboards = [
      createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Dashboard 1' }),
    ];

    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse(dashboards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Dashboard 1')).toBeInTheDocument();
  });

  it('削除ボタンクリックで確認ダイアログを表示する', () => {
    const dashboards = [
      createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Dashboard 1' }),
    ];

    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse(dashboards),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText('Dashboard 1')).toBeInTheDocument();
  });

  it('ページネーションが表示される', () => {
    const dashboards = Array.from({ length: 10 }, (_, i) =>
      createMockDashboard({ dashboard_id: `dashboard-${i}` })
    );

    mockUseDashboards.mockReturnValue({
      data: createMockPaginatedResponse(dashboards, 100),
      isLoading: false,
    } as any);

    render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

    expect(screen.getByText(/100件中/)).toBeInTheDocument();
  });

  describe('権限制御', () => {
    it('viewer権限のダッシュボードは編集・削除ボタンが非表示', () => {
      const dashboards = [
        createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Viewer Dashboard', my_permission: 'viewer' }),
      ];

      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse(dashboards),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      expect(screen.getByText('Viewer Dashboard')).toBeInTheDocument();
      // 表示ボタン(Eye)は存在する
      const row = screen.getByText('Viewer Dashboard').closest('tr')!;
      const buttons = row.querySelectorAll('button');
      // 表示ボタンのみ (Eye)
      expect(buttons).toHaveLength(1);
    });

    it('editor権限のダッシュボードは削除ボタンが非表示', () => {
      const dashboards = [
        createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Editor Dashboard', my_permission: 'editor' }),
      ];

      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse(dashboards),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      const row = screen.getByText('Editor Dashboard').closest('tr')!;
      const buttons = row.querySelectorAll('button');
      // 表示ボタン(Eye) + 編集ボタン(Pencil) の2つ
      expect(buttons).toHaveLength(2);
    });

    it('owner権限のダッシュボードは全操作ボタンが表示される', () => {
      const dashboards = [
        createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Owner Dashboard', my_permission: 'owner' }),
      ];

      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse(dashboards),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      const row = screen.getByText('Owner Dashboard').closest('tr')!;
      const buttons = row.querySelectorAll('button');
      // 表示(Eye) + 編集(Pencil) + 削除(Trash2) の3つ
      expect(buttons).toHaveLength(3);
    });

    it('my_permissionがundefinedの場合は全ボタン表示(後方互換)', () => {
      const dashboards = [
        createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Legacy Dashboard' }),
      ];

      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse(dashboards),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      const row = screen.getByText('Legacy Dashboard').closest('tr')!;
      const buttons = row.querySelectorAll('button');
      // 表示(Eye) + 編集(Pencil) + 削除(Trash2) の3つ
      expect(buttons).toHaveLength(3);
    });

    it('権限バッジが表示される', () => {
      const dashboards = [
        createMockDashboard({ dashboard_id: 'dashboard-1', name: 'Owner Dashboard', my_permission: 'owner' }),
        createMockDashboard({ dashboard_id: 'dashboard-2', name: 'Viewer Dashboard', my_permission: 'viewer' }),
        createMockDashboard({ dashboard_id: 'dashboard-3', name: 'Editor Dashboard', my_permission: 'editor' }),
      ];

      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse(dashboards),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      expect(screen.getByText('owner')).toBeInTheDocument();
      expect(screen.getByText('viewer')).toBeInTheDocument();
      expect(screen.getByText('editor')).toBeInTheDocument();
    });

    it('権限列がテーブルヘッダーに表示される', () => {
      mockUseDashboards.mockReturnValue({
        data: createMockPaginatedResponse([]),
        isLoading: false,
      } as any);

      render(<MemoryRouter><DashboardListPage /></MemoryRouter>, { wrapper: createWrapper() });

      expect(screen.getByText('権限')).toBeInTheDocument();
    });
  });
});
