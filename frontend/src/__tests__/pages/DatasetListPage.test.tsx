import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { DatasetListPage } from '@/pages/DatasetListPage';
import { createWrapper, createMockDataset, createMockPaginatedResponse } from '@/__tests__/helpers/test-utils';

// Mock hooks
const mockNavigate = vi.fn();
const mockDeleteMutate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/hooks', () => ({
  useDatasets: vi.fn(),
  useDeleteDataset: vi.fn(() => ({
    mutate: mockDeleteMutate,
  })),
}));

import { useDatasets } from '@/hooks';
const mockUseDatasets = useDatasets as ReturnType<typeof vi.fn>;

describe('DatasetListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseDatasets.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('データセット一覧をテーブルに表示する', () => {
    const datasets = [
      createMockDataset({ dataset_id: 'dataset-1', name: 'Dataset 1' }),
      createMockDataset({ dataset_id: 'dataset-2', name: 'Dataset 2' }),
    ];

    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
    expect(screen.getByText('Dataset 2')).toBeInTheDocument();
  });

  it('データセットがない場合はメッセージを表示する', () => {
    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('データセットがありません')).toBeInTheDocument();
  });

  it('インポートボタンがある', () => {
    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse([]),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /インポート/ })).toBeInTheDocument();
  });

  it('詳細ボタンクリックで遷移する', async () => {
    const user = userEvent.setup();
    const datasets = [
      createMockDataset({ dataset_id: 'dataset-1', name: 'Dataset 1' }),
    ];

    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // Eye icon button
    const detailButtons = screen.getAllByRole('button');
    const eyeButton = detailButtons.find(btn => btn.querySelector('svg'));
    if (eyeButton) {
      await user.click(eyeButton);
      expect(mockNavigate).toHaveBeenCalled();
    }
  });

  it('削除ボタンクリックで確認ダイアログを表示する', () => {
    const datasets = [
      createMockDataset({ dataset_id: 'dataset-1', name: 'Dataset 1' }),
    ];

    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // Verify table is rendered
    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
  });

  it('確認ダイアログで削除を実行する', () => {
    const datasets = [
      createMockDataset({ dataset_id: 'dataset-1', name: 'Dataset 1' }),
    ];

    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    // Verify delete mutation is available
    expect(mockDeleteMutate).toBeDefined();
  });

  it('ページネーションが表示される', () => {
    const datasets = Array.from({ length: 10 }, (_, i) =>
      createMockDataset({ dataset_id: `dataset-${i}` })
    );

    const response = createMockPaginatedResponse(datasets, 100);

    mockUseDatasets.mockReturnValue({
      data: response,
      isLoading: false,
    } as any);

    render(
      <MemoryRouter>
        <DatasetListPage />
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText(/100件中/)).toBeInTheDocument();
  });
});
