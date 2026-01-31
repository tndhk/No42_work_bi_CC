import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DashboardViewPage } from '@/pages/DashboardViewPage';
import { createWrapper, createMockDashboard } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();
const mockExecuteCard = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ dashboardId: 'dashboard-1' }),
  };
});

vi.mock('@/hooks', () => ({
  useDashboard: vi.fn(),
  useExecuteCard: vi.fn(() => ({ mutateAsync: mockExecuteCard })),
}));

vi.mock('@/components/dashboard/DashboardViewer', () => ({
  DashboardViewer: ({ dashboard, filters }: any) => (
    <div data-testid="dashboard-viewer" data-filters={JSON.stringify(filters || {})}>
      Viewing {dashboard.name}
    </div>
  ),
}));

vi.mock('@/components/dashboard/FilterBar', () => ({
  FilterBar: ({ filters, values, onClearAll }: any) => (
    <div data-testid="filter-bar">
      {filters.length} filters, {Object.keys(values).length} active
      <button onClick={onClearAll}>Clear</button>
    </div>
  ),
}));

import { useDashboard } from '@/hooks';
const mockUseDashboard = useDashboard as ReturnType<typeof vi.fn>;

describe('DashboardViewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseDashboard.mockReturnValue({ data: undefined, isLoading: true } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('ダッシュボードが見つからない場合はメッセージを表示する', () => {
    mockUseDashboard.mockReturnValue({ data: null, isLoading: false, isError: true } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('ダッシュボードが見つかりません')).toBeInTheDocument();
  });

  it('ダッシュボード名を表示する', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, cards: [], filters: [] },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
  });

  it('編集ボタンがある', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, cards: [], filters: [] },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /編集/ })).toBeInTheDocument();
  });

  it('DashboardViewerにダッシュボードを渡す', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, cards: [], filters: [] },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('dashboard-viewer')).toBeInTheDocument();
    expect(screen.getByText(/Viewing Test Dashboard/)).toBeInTheDocument();
  });

  it('フィルタがある場合はフィルタトグルボタンを表示する', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: {
        ...dashboard,
        cards: [],
        filters: [{ id: 'f1', type: 'category', column: 'region', label: 'Region', options: ['East'] }],
      },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByLabelText('フィルタ表示切替')).toBeInTheDocument();
  });

  it('フィルタがない場合はフィルタトグルボタンを表示しない', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, cards: [], filters: [] },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByLabelText('フィルタ表示切替')).not.toBeInTheDocument();
  });

  it('フィルタがある場合はFilterBarを表示する', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: {
        ...dashboard,
        cards: [],
        filters: [{ id: 'f1', type: 'category', column: 'region', label: 'Region', options: ['East'] }],
      },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('filter-bar')).toBeInTheDocument();
  });

  it('フィルタトグルでFilterBarの表示を切り替える', async () => {
    const user = userEvent.setup();
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: {
        ...dashboard,
        cards: [],
        filters: [{ id: 'f1', type: 'category', column: 'region', label: 'Region', options: ['East'] }],
      },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
        <Routes>
          <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // Initially visible
    expect(screen.getByTestId('filter-bar')).toBeInTheDocument();

    // Toggle off
    await user.click(screen.getByLabelText('フィルタ表示切替'));
    expect(screen.queryByTestId('filter-bar')).not.toBeInTheDocument();

    // Toggle on
    await user.click(screen.getByLabelText('フィルタ表示切替'));
    expect(screen.getByTestId('filter-bar')).toBeInTheDocument();
  });
});
