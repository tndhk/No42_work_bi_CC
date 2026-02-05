import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DatasetDetailPage } from '@/pages/DatasetDetailPage';
import { createWrapper, createMockDataset } from '@/__tests__/helpers/test-utils';
import type { SchemaChange, ReimportDryRunResponse } from '@/types/reimport';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'dataset-1' }),
  };
});

const mockReimportDryRunMutateAsync = vi.fn();
const mockReimportDatasetMutateAsync = vi.fn();

vi.mock('@/hooks', () => ({
  useDataset: vi.fn(() => ({ data: null, isLoading: false })),
  useDatasetPreview: vi.fn(() => ({ data: null, isLoading: false })),
  useReimportDryRun: vi.fn(() => ({
    mutateAsync: mockReimportDryRunMutateAsync,
    isPending: false,
  })),
  useReimportDataset: vi.fn(() => ({
    mutateAsync: mockReimportDatasetMutateAsync,
    isPending: false,
  })),
}));

vi.mock('@/components/datasets/SchemaChangeWarningDialog', () => ({
  SchemaChangeWarningDialog: vi.fn(({ open, changes, onConfirm, onCancel }) => {
    if (!open) return null;
    return (
      <div data-testid="schema-change-warning-dialog">
        <div data-testid="schema-changes-count">{changes.length}</div>
        <button data-testid="dialog-confirm" onClick={onConfirm}>続行</button>
        <button data-testid="dialog-cancel" onClick={onCancel}>キャンセル</button>
      </div>
    );
  }),
}));

import { useDataset, useDatasetPreview, useReimportDryRun, useReimportDataset } from '@/hooks';
const mockUseDataset = useDataset as ReturnType<typeof vi.fn>;
const mockUseDatasetPreview = useDatasetPreview as ReturnType<typeof vi.fn>;
const mockUseReimportDryRun = useReimportDryRun as ReturnType<typeof vi.fn>;
const mockUseReimportDataset = useReimportDataset as ReturnType<typeof vi.fn>;

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
        id: 'dataset-1',
        name: 'Test Dataset',
        row_count: 1000,
        column_count: 5,
      }),
      columns: [],
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
        id: 'dataset-1',
        name: 'Test Dataset',
      }),
      columns: [],
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
        id: 'dataset-1',
        name: 'Test Dataset',
      }),
      columns: [],
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

describe('再取り込み機能', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockReimportDryRunMutateAsync.mockReset();
    mockReimportDatasetMutateAsync.mockReset();
    mockUseReimportDryRun.mockReturnValue({
      mutateAsync: mockReimportDryRunMutateAsync,
      isPending: false,
    });
    mockUseReimportDataset.mockReturnValue({
      mutateAsync: mockReimportDatasetMutateAsync,
      isPending: false,
    });
  });

  afterEach(() => {
    cleanup();
  });

  const createS3CsvDataset = (overrides?: Record<string, unknown>) => ({
    ...createMockDataset({
      id: 'dataset-1',
      name: 'S3 CSV Dataset',
      source_type: 's3_csv',
    }),
    columns: [{ name: 'id', data_type: 'INTEGER', nullable: false }],
    s3_path: 's3://bucket/path/file.csv',
    ...overrides,
  });

  const createCsvDataset = (overrides?: Record<string, unknown>) => ({
    ...createMockDataset({
      id: 'dataset-1',
      name: 'CSV Dataset',
      source_type: 'csv',
    }),
    columns: [{ name: 'id', data_type: 'INTEGER', nullable: false }],
    ...overrides,
  });

  it('source_type が s3_csv の場合、再取り込みボタンが表示される', () => {
    const dataset = createS3CsvDataset();
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

    expect(screen.getByRole('button', { name: /再取り込み/ })).toBeInTheDocument();
  });

  it('source_type が s3_csv 以外の場合、再取り込みボタンは表示されない', () => {
    const dataset = createCsvDataset();
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

    expect(screen.queryByRole('button', { name: /再取り込み/ })).not.toBeInTheDocument();
  });

  it('再取り込みボタンをクリックするとdry-runが実行される', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const dryRunResponse: ReimportDryRunResponse = {
      has_schema_changes: false,
      changes: [],
      new_row_count: 100,
      new_column_count: 5,
    };
    mockReimportDryRunMutateAsync.mockResolvedValue(dryRunResponse);
    mockReimportDatasetMutateAsync.mockResolvedValue({});

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(mockReimportDryRunMutateAsync).toHaveBeenCalledWith('dataset-1');
    });
  });

  it('スキーマ変更がある場合、警告ダイアログが表示される', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'new_col', change_type: 'added', old_value: null, new_value: 'TEXT' },
    ];
    const dryRunResponse: ReimportDryRunResponse = {
      has_schema_changes: true,
      changes: schemaChanges,
      new_row_count: 150,
      new_column_count: 6,
    };
    mockReimportDryRunMutateAsync.mockResolvedValue(dryRunResponse);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();
    });
  });

  it('スキーマ変更がない場合、即座に再取り込みが実行される', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const dryRunResponse: ReimportDryRunResponse = {
      has_schema_changes: false,
      changes: [],
      new_row_count: 100,
      new_column_count: 5,
    };
    mockReimportDryRunMutateAsync.mockResolvedValue(dryRunResponse);
    mockReimportDatasetMutateAsync.mockResolvedValue({});

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(mockReimportDatasetMutateAsync).toHaveBeenCalledWith({
        datasetId: 'dataset-1',
        force: false,
      });
    });
  });

  it('警告ダイアログで「続行」をクリックすると再取り込みが実行される', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'removed_col', change_type: 'removed', old_value: 'TEXT', new_value: null },
    ];
    const dryRunResponse: ReimportDryRunResponse = {
      has_schema_changes: true,
      changes: schemaChanges,
      new_row_count: 100,
      new_column_count: 4,
    };
    mockReimportDryRunMutateAsync.mockResolvedValue(dryRunResponse);
    mockReimportDatasetMutateAsync.mockResolvedValue({});

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();
    });

    const confirmButton = screen.getByTestId('dialog-confirm');
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockReimportDatasetMutateAsync).toHaveBeenCalledWith({
        datasetId: 'dataset-1',
        force: true,
      });
    });
  });

  it('警告ダイアログで「キャンセル」をクリックするとダイアログが閉じる', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'type_col', change_type: 'type_changed', old_value: 'TEXT', new_value: 'INTEGER' },
    ];
    const dryRunResponse: ReimportDryRunResponse = {
      has_schema_changes: true,
      changes: schemaChanges,
      new_row_count: 100,
      new_column_count: 5,
    };
    mockReimportDryRunMutateAsync.mockResolvedValue(dryRunResponse);

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();
    });

    const cancelButton = screen.getByTestId('dialog-cancel');
    await user.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByTestId('schema-change-warning-dialog')).not.toBeInTheDocument();
    });

    // 再取り込みは実行されない
    expect(mockReimportDatasetMutateAsync).not.toHaveBeenCalled();
  });

  it('再取り込み中はボタンが無効化される', () => {
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseReimportDryRun.mockReturnValue({
      mutateAsync: mockReimportDryRunMutateAsync,
      isPending: true,
    });
    mockUseReimportDataset.mockReturnValue({
      mutateAsync: mockReimportDatasetMutateAsync,
      isPending: false,
    });

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    expect(reimportButton).toBeDisabled();
  });
});
