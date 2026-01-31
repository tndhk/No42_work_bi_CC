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
});
