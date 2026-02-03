import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DashboardViewPage } from '@/pages/DashboardViewPage';
import { createWrapper, createMockDashboard, setupAuthState, createMockUser, clearAuthState } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();
const mockExecuteCard = vi.fn();
const mockCreateFilterView = vi.fn();
const mockUpdateFilterView = vi.fn();
const mockDeleteFilterView = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'dashboard-1' }),
  };
});

vi.mock('@/hooks', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/hooks')>();
  return {
    ...actual,
    useDashboard: vi.fn(),
    useExecuteCard: vi.fn(() => ({ mutateAsync: mockExecuteCard })),
    useFilterViews: vi.fn(() => ({ data: [], isLoading: false })),
    useCreateFilterView: vi.fn(() => ({ mutateAsync: mockCreateFilterView })),
    useUpdateFilterView: vi.fn(() => ({ mutateAsync: mockUpdateFilterView })),
    useDeleteFilterView: vi.fn(() => ({ mutateAsync: mockDeleteFilterView })),
  };
});

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

vi.mock('@/components/dashboard/ShareDialog', () => ({
  ShareDialog: ({ open, onOpenChange, dashboardId }: any) => (
    open ? <div data-testid="share-dialog">Share for {dashboardId}<button onClick={() => onOpenChange(false)}>Close</button></div> : null
  ),
}));

vi.mock('@/components/dashboard/FilterViewSelector', () => ({
  FilterViewSelector: ({ views, selectedViewId, onSelect, onSave, onOverwrite, onDelete }: any) => (
    <div data-testid="filter-view-selector">
      <button aria-label="ビュー" onClick={() => {}}>ビュー</button>
      <span data-testid="view-count">{views.length}</span>
      {selectedViewId && <span data-testid="selected-view-id">{selectedViewId}</span>}
      {views.map((v: any) => (
        <button key={v.id} data-testid={`select-view-${v.id}`} onClick={() => onSelect(v)}>
          {v.name}
        </button>
      ))}
      <button data-testid="save-view" onClick={() => onSave('New View')}>Save</button>
      {selectedViewId && (
        <>
          <button data-testid="overwrite-view" onClick={() => onOverwrite(selectedViewId)}>Overwrite</button>
          <button data-testid="delete-view" onClick={() => onDelete(selectedViewId)}>Delete</button>
        </>
      )}
    </div>
  ),
}));

import { useDashboard, useFilterViews } from '@/hooks';
const mockUseDashboard = useDashboard as ReturnType<typeof vi.fn>;
const mockUseFilterViews = useFilterViews as ReturnType<typeof vi.fn>;

describe('DashboardViewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseFilterViews.mockReturnValue({ data: [], isLoading: false });
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

  describe('FilterView Integration', () => {
    const dashboardWithFilters = () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
      });
      return {
        ...dashboard,
        cards: [],
        filters: [{ id: 'f1', type: 'category', column: 'region', label: 'Region', options: ['East'] }],
      };
    };

    it('フィルタがある場合にFilterViewSelectorを表示する', () => {
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      expect(screen.getByTestId('filter-view-selector')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /ビュー/i })).toBeInTheDocument();
    });

    it('フィルタがない場合はFilterViewSelectorを表示しない', () => {
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

      expect(screen.queryByTestId('filter-view-selector')).not.toBeInTheDocument();
    });

    it('useFilterViewsをダッシュボードIDで呼び出す', () => {
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      expect(mockUseFilterViews).toHaveBeenCalledWith('dashboard-1');
    });

    it('ビューを選択するとフィルタ値が復元される', async () => {
      const user = userEvent.setup();
      const mockViews = [
        {
          id: 'view-1',
          dashboard_id: 'dashboard-1',
          name: 'East Region',
          owner_id: 'user-1',
          filter_state: { f1: 'East' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // Click to select the view
      await user.click(screen.getByTestId('select-view-view-1'));

      // After selecting, the selected view ID should be tracked
      expect(screen.getByTestId('selected-view-id')).toHaveTextContent('view-1');

      // The filter values should be restored (visible in DashboardViewer data-filters)
      expect(screen.getByTestId('dashboard-viewer').getAttribute('data-filters')).toBe(
        JSON.stringify({ f1: 'East' })
      );
    });

    it('新しいビューを保存できる', async () => {
      const user = userEvent.setup();
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      await user.click(screen.getByTestId('save-view'));

      expect(mockCreateFilterView).toHaveBeenCalledWith({
        dashboardId: 'dashboard-1',
        data: {
          name: 'New View',
          filter_state: {},
        },
      });
    });

    it('選択中のビューを上書き保存できる', async () => {
      const user = userEvent.setup();
      const mockViews = [
        {
          id: 'view-1',
          dashboard_id: 'dashboard-1',
          name: 'East Region',
          owner_id: 'user-1',
          filter_state: { f1: 'East' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // First select the view
      await user.click(screen.getByTestId('select-view-view-1'));

      // Then overwrite
      await user.click(screen.getByTestId('overwrite-view'));

      expect(mockUpdateFilterView).toHaveBeenCalledWith({
        filterViewId: 'view-1',
        data: {
          filter_state: { f1: 'East' },
        },
      });
    });

    it('選択中のビューを削除できる', async () => {
      const user = userEvent.setup();
      const mockViews = [
        {
          id: 'view-1',
          dashboard_id: 'dashboard-1',
          name: 'East Region',
          owner_id: 'user-1',
          filter_state: { f1: 'East' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // First select the view
      await user.click(screen.getByTestId('select-view-view-1'));

      // Then delete
      await user.click(screen.getByTestId('delete-view'));

      expect(mockDeleteFilterView).toHaveBeenCalledWith('view-1');
    });

    it('削除後にselectedViewIdがクリアされる', async () => {
      const user = userEvent.setup();
      const mockViews = [
        {
          id: 'view-1',
          dashboard_id: 'dashboard-1',
          name: 'East Region',
          owner_id: 'user-1',
          filter_state: { f1: 'East' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // Select view
      await user.click(screen.getByTestId('select-view-view-1'));
      expect(screen.getByTestId('selected-view-id')).toBeInTheDocument();

      // Delete
      await user.click(screen.getByTestId('delete-view'));

      // After deletion, selectedViewId should be cleared
      expect(screen.queryByTestId('selected-view-id')).not.toBeInTheDocument();
    });

    it('フィルタクリア時にselectedViewIdもクリアされる', async () => {
      const user = userEvent.setup();
      const mockViews = [
        {
          id: 'view-1',
          dashboard_id: 'dashboard-1',
          name: 'East Region',
          owner_id: 'user-1',
          filter_state: { f1: 'East' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // Select view
      await user.click(screen.getByTestId('select-view-view-1'));
      expect(screen.getByTestId('selected-view-id')).toBeInTheDocument();

      // Clear all filters via FilterBar
      await user.click(screen.getByText('Clear'));

      // selectedViewId should be cleared
      expect(screen.queryByTestId('selected-view-id')).not.toBeInTheDocument();
    });

    it('初回ロード時にデフォルトビューが自動適用される', () => {
      const currentUserId = 'user-1';

      // 現在のユーザーをセットアップ
      setupAuthState('test-token', createMockUser({ user_id: currentUserId }));

      const mockViews = [
        {
          id: 'view-normal',
          dashboard_id: 'dashboard-1',
          name: 'Normal View',
          owner_id: currentUserId,
          filter_state: { f1: 'Normal' },
          is_shared: false,
          is_default: false,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        {
          id: 'view-default',
          dashboard_id: 'dashboard-1',
          name: 'Default View',
          owner_id: currentUserId,
          filter_state: { f1: 'DefaultValue' },
          is_shared: false,
          is_default: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // デフォルトビューが自動的に選択される
      expect(screen.getByTestId('selected-view-id')).toHaveTextContent('view-default');

      // デフォルトビューのフィルタ値が適用される
      expect(screen.getByTestId('dashboard-viewer').getAttribute('data-filters')).toBe(
        JSON.stringify({ f1: 'DefaultValue' })
      );

      // クリーンアップ
      clearAuthState();
    });

    it('自分のデフォルトビューが共有デフォルトより優先される', () => {
      const currentUserId = 'current-user';

      // 現在のユーザーをセットアップ
      setupAuthState('test-token', createMockUser({ user_id: currentUserId }));

      const mockViews = [
        {
          id: 'view-shared-default',
          dashboard_id: 'dashboard-1',
          name: 'Shared Default View',
          owner_id: 'other-user',
          filter_state: { f1: 'SharedDefault' },
          is_shared: true,
          is_default: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        {
          id: 'view-own-default',
          dashboard_id: 'dashboard-1',
          name: 'My Default View',
          owner_id: currentUserId,
          filter_state: { f1: 'OwnDefault' },
          is_shared: false,
          is_default: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ];

      mockUseFilterViews.mockReturnValue({ data: mockViews, isLoading: false });
      mockUseDashboard.mockReturnValue({
        data: dashboardWithFilters(),
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

      // 自分のデフォルトビューが優先される
      expect(screen.getByTestId('selected-view-id')).toHaveTextContent('view-own-default');

      // 自分のデフォルトビューのフィルタ値が適用される
      expect(screen.getByTestId('dashboard-viewer').getAttribute('data-filters')).toBe(
        JSON.stringify({ f1: 'OwnDefault' })
      );

      // クリーンアップ
      clearAuthState();
    });
  });

  describe('権限制御', () => {
    const renderViewPage = () => {
      return render(
        <MemoryRouter initialEntries={['/dashboards/dashboard-1']}>
          <Routes>
            <Route path="/dashboards/:dashboardId" element={<DashboardViewPage />} />
          </Routes>
        </MemoryRouter>,
        { wrapper: createWrapper() }
      );
    };

    it('viewer権限で編集ボタンが非表示', () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        my_permission: 'viewer',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      expect(screen.getByText('Test Dashboard')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /編集/ })).not.toBeInTheDocument();
    });

    it('editor権限で編集ボタンが表示される', () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        my_permission: 'editor',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      expect(screen.getByRole('button', { name: /編集/ })).toBeInTheDocument();
    });

    it('owner権限で編集ボタンと共有ボタンが表示される', async () => {
      const user = userEvent.setup();
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        my_permission: 'owner',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      expect(screen.getByRole('button', { name: /編集/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /共有/ })).toBeInTheDocument();

      // 共有ボタンクリックでShareDialogが開く
      await user.click(screen.getByRole('button', { name: /共有/ }));
      expect(screen.getByTestId('share-dialog')).toBeInTheDocument();
    });

    it('viewer権限では共有ボタンが非表示', () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        my_permission: 'viewer',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      expect(screen.queryByRole('button', { name: /共有/ })).not.toBeInTheDocument();
    });

    it('editor権限では共有ボタンが非表示', () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
        my_permission: 'editor',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      expect(screen.queryByRole('button', { name: /共有/ })).not.toBeInTheDocument();
    });

    it('my_permissionがundefinedの場合は全ボタン表示(後方互換)', () => {
      const dashboard = createMockDashboard({
        dashboard_id: 'dashboard-1',
        name: 'Test Dashboard',
      });

      mockUseDashboard.mockReturnValue({
        data: { ...dashboard, cards: [], filters: [] },
        isLoading: false,
      } as any);

      renderViewPage();

      // 後方互換: 全ボタン表示
      expect(screen.getByRole('button', { name: /編集/ })).toBeInTheDocument();
    });
  });
});
