import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TransformEditPage } from '@/pages/TransformEditPage';
import { createWrapper, createMockPaginatedResponse, createMockDataset } from '@/__tests__/helpers/test-utils';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'new' }),
  };
});

vi.mock('@/hooks', () => ({
  useTransform: vi.fn(() => ({ data: null, isLoading: false })),
  useDatasets: vi.fn(() => ({ data: null })),
  useCreateTransform: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useUpdateTransform: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useExecuteTransform: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useTransformExecutions: vi.fn(() => ({ data: null, isLoading: false })),
}));

vi.mock('@/components/transform/TransformCodeEditor', () => ({
  TransformCodeEditor: ({ code, onChange }: any) => (
    <textarea data-testid="transform-code-editor" value={code} onChange={(e) => onChange(e.target.value)} />
  ),
}));

vi.mock('@/components/transform/DatasetMultiSelect', () => ({
  DatasetMultiSelect: ({ datasets, selectedIds, onChange }: any) => (
    <div data-testid="dataset-multi-select">
      {datasets?.map((ds: any) => (
        <label key={ds.dataset_id}>
          <input
            type="checkbox"
            checked={selectedIds.includes(ds.dataset_id)}
            onChange={() => {
              if (selectedIds.includes(ds.dataset_id)) {
                onChange(selectedIds.filter((id: string) => id !== ds.dataset_id));
              } else {
                onChange([...selectedIds, ds.dataset_id]);
              }
            }}
          />
          {ds.name}
        </label>
      ))}
    </div>
  ),
}));

vi.mock('@/components/transform/TransformExecutionResult', () => ({
  TransformExecutionResult: ({ result }: any) => (
    result ? <div data-testid="execution-result">Result</div> : null
  ),
}));

vi.mock('@/components/transform/TransformExecutionHistory', () => ({
  TransformExecutionHistory: () => <div data-testid="execution-history">History</div>,
}));

vi.mock('@/components/transform/TransformScheduleConfig', () => ({
  TransformScheduleConfig: () => <div data-testid="schedule-config">Schedule Config</div>,
}));

import { useTransform, useDatasets } from '@/hooks';
const mockUseTransform = useTransform as ReturnType<typeof vi.fn>;
const mockUseDatasets = useDatasets as ReturnType<typeof vi.fn>;

describe('TransformEditPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('新規作成モードで「新規Transform」を表示する', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('新規Transform')).toBeInTheDocument();
  });

  it('Transform名入力フィールドがある', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Transform名')).toBeInTheDocument();
  });

  it('入力データセット選択がある', () => {
    const datasets = [createMockDataset({ dataset_id: 'ds-1', name: 'Dataset 1' })];
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({
      data: createMockPaginatedResponse(datasets),
    } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('入力データセット')).toBeInTheDocument();
    expect(screen.getByTestId('dataset-multi-select')).toBeInTheDocument();
  });

  it('Pythonコードエディタがある', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Pythonコード')).toBeInTheDocument();
    expect(screen.getByTestId('transform-code-editor')).toBeInTheDocument();
  });

  it('保存ボタンがある', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('button', { name: /保存/ })).toBeInTheDocument();
  });

  it('戻るボタンがある', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const backButtons = screen.getAllByRole('button');
    expect(backButtons.length).toBeGreaterThan(0);
  });

  it('実行結果セクションがある', () => {
    mockUseTransform.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseDatasets.mockReturnValue({ data: null } as any);

    render(
      <MemoryRouter initialEntries={['/transforms/new']}>
        <Routes>
          <Route path="/transforms/:id" element={<TransformEditPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('実行結果')).toBeInTheDocument();
  });
});
