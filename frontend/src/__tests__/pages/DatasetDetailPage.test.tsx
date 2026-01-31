import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DatasetDetailPage } from '@/pages/DatasetDetailPage';
import { createWrapper, createMockDataset } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'dataset-1' }),
  };
});

vi.mock('@/hooks', () => ({
  useDataset: vi.fn(() => ({ data: null, isLoading: false })),
  useDatasetPreview: vi.fn(() => ({ data: null, isLoading: false })),
}));

import { useDataset, useDatasetPreview } from '@/hooks';
const mockUseDataset = useDataset as ReturnType<typeof vi.fn>;
const mockUseDatasetPreview = useDatasetPreview as ReturnType<typeof vi.fn>;

describe('DatasetDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('ローディング中はスピナーを表示する', () => {
    mockUseDataset.mockReturnValue({ data: null, isLoading: true } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('データセットが見つからない場合はメッセージを表示する', () => {
    mockUseDataset.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('データセットが見つかりません')).toBeInTheDocument();
  });

  it('データセット名と行列数を表示する', () => {
    const dataset = {
      ...createMockDataset({
        dataset_id: 'dataset-1',
        name: 'Test Dataset',
        row_count: 1000,
        column_count: 5,
      }),
      schema: [],
    };

    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Test Dataset')).toBeInTheDocument();
    expect(screen.getByText(/1,000行/)).toBeInTheDocument();
  });

  it('スキーマセクションを表示する', () => {
    const dataset = {
      ...createMockDataset({
        dataset_id: 'dataset-1',
        name: 'Test Dataset',
      }),
      schema: [],
    };

    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('スキーマ')).toBeInTheDocument();
  });

  it('戻るボタンがある', () => {
    const dataset = {
      ...createMockDataset({
        dataset_id: 'dataset-1',
        name: 'Test Dataset',
      }),
      schema: [],
    };

    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const backButtons = screen.getAllByRole('button');
    expect(backButtons.length).toBeGreaterThan(0);
  });
});
