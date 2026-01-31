import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DashboardEditPage } from '@/pages/DashboardEditPage';
import { createWrapper, createMockDashboard } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'dashboard-1' }),
  };
});

vi.mock('@/hooks', () => ({
  useDashboard: vi.fn(() => ({ data: null, isLoading: false })),
  useUpdateDashboard: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

vi.mock('@/components/dashboard/DashboardEditor', () => ({
  DashboardEditor: ({ layout }: any) => (
    <div data-testid="dashboard-editor">Editor with {layout.cards.length} cards</div>
  ),
}));

vi.mock('@/components/dashboard/AddCardDialog', () => ({
  AddCardDialog: () => <div data-testid="add-card-dialog">Add Card Dialog</div>,
}));

import { useDashboard } from '@/hooks';
const mockUseDashboard = useDashboard as ReturnType<typeof vi.fn>;

describe('DashboardEditPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseDashboard.mockReturnValue({ data: null, isLoading: true } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('ダッシュボードが見つからない場合はメッセージを表示する', () => {
    mockUseDashboard.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('ダッシュボードが見つかりません')).toBeInTheDocument();
  });

  it('ダッシュボード名入力フィールドがある', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, layout: { cards: [], columns: 12, row_height: 100 } },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const nameInput = screen.getByDisplayValue('Test Dashboard');
    expect(nameInput).toBeInTheDocument();
  });

  it('カード追加ボタンがある', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, layout: { cards: [], columns: 12, row_height: 100 } },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /カード追加/ })).toBeInTheDocument();
  });

  it('保存ボタンがある', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, layout: { cards: [], columns: 12, row_height: 100 } },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /保存/ })).toBeInTheDocument();
  });

  it('DashboardEditorを表示する', () => {
    const dashboard = createMockDashboard({
      dashboard_id: 'dashboard-1',
      name: 'Test Dashboard',
    });

    mockUseDashboard.mockReturnValue({
      data: { ...dashboard, layout: { cards: [], columns: 12, row_height: 100 } },
      isLoading: false,
    } as any);

    render(
      <MemoryRouter initialEntries={['/dashboards/dashboard-1/edit']}>
        <Routes>
          <Route path="/dashboards/:id/edit" element={<DashboardEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('dashboard-editor')).toBeInTheDocument();
  });
});
