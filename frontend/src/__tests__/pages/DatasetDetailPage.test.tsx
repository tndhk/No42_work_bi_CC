import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DatasetDetailPage } from '@/pages/DatasetDetailPage';
import { createWrapper, createMockDataset } from '@/__tests__/helpers/test-utils';
import type { SchemaChange } from '@/types/reimport';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: 'dataset-1' }),
  };
});

const mockHandleReimport = vi.fn();
const mockHandleConfirm = vi.fn();
const mockHandleCancel = vi.fn();

vi.mock('@/hooks', () => ({
  useDataset: vi.fn(() => ({ data: null, isLoading: false })),
  useDatasetPreview: vi.fn(() => ({ data: null, isLoading: false })),
}));

vi.mock('@/hooks/use-reimport-flow', () => ({
  useReimportFlow: vi.fn(() => ({
    dialogOpen: false,
    changes: [],
    isPending: false,
    handleReimport: mockHandleReimport,
    handleConfirm: mockHandleConfirm,
    handleCancel: mockHandleCancel,
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

import { useDataset, useDatasetPreview } from '@/hooks';
import { useReimportFlow } from '@/hooks/use-reimport-flow';

const mockUseDataset = useDataset as ReturnType<typeof vi.fn>;
const mockUseDatasetPreview = useDatasetPreview as ReturnType<typeof vi.fn>;
const mockUseReimportFlow = useReimportFlow as ReturnType<typeof vi.fn>;

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
    mockHandleReimport.mockReset();
    mockHandleConfirm.mockReset();
    mockHandleCancel.mockReset();
    mockUseReimportFlow.mockReturnValue({
      dialogOpen: false,
      changes: [],
      isPending: false,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
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

  it('再取り込みボタンをクリックするとhandleReimportが呼ばれる', async () => {
    const user = userEvent.setup();
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

    const reimportButton = screen.getByRole('button', { name: /再取り込み/ });
    await user.click(reimportButton);

    await waitFor(() => {
      expect(mockHandleReimport).toHaveBeenCalled();
    });
  });

  it('スキーマ変更がある場合、警告ダイアログが表示される', async () => {
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'new_col', change_type: 'added', old_value: null, new_value: 'TEXT' },
    ];
    mockUseReimportFlow.mockReturnValue({
      dialogOpen: true,
      changes: schemaChanges,
      isPending: false,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
    });

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();
  });

  it('スキーマ変更がない場合、ダイアログは表示されない', async () => {
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    mockUseReimportFlow.mockReturnValue({
      dialogOpen: false,
      changes: [],
      isPending: false,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
    });

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByTestId('schema-change-warning-dialog')).not.toBeInTheDocument();
  });

  it('警告ダイアログで「続行」をクリックするとhandleConfirmが呼ばれる', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'removed_col', change_type: 'removed', old_value: 'TEXT', new_value: null },
    ];
    mockUseReimportFlow.mockReturnValue({
      dialogOpen: true,
      changes: schemaChanges,
      isPending: false,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
    });

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();

    const confirmButton = screen.getByTestId('dialog-confirm');
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockHandleConfirm).toHaveBeenCalled();
    });
  });

  it('警告ダイアログで「キャンセル」をクリックするとhandleCancelが呼ばれる', async () => {
    const user = userEvent.setup();
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);

    const schemaChanges: SchemaChange[] = [
      { column_name: 'type_col', change_type: 'type_changed', old_value: 'TEXT', new_value: 'INTEGER' },
    ];
    mockUseReimportFlow.mockReturnValue({
      dialogOpen: true,
      changes: schemaChanges,
      isPending: false,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
    });

    render(
      <MemoryRouter initialEntries={['/datasets/dataset-1']}>
        <Routes>
          <Route path="/datasets/:id" element={<DatasetDetailPage />} />
        </Routes>
      </MemoryRouter>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('schema-change-warning-dialog')).toBeInTheDocument();

    const cancelButton = screen.getByTestId('dialog-cancel');
    await user.click(cancelButton);

    await waitFor(() => {
      expect(mockHandleCancel).toHaveBeenCalled();
    });
  });

  it('再取り込み中はボタンが無効化される', () => {
    const dataset = createS3CsvDataset();
    mockUseDataset.mockReturnValue({ data: dataset, isLoading: false } as any);
    mockUseDatasetPreview.mockReturnValue({ data: null, isLoading: false } as any);
    mockUseReimportFlow.mockReturnValue({
      dialogOpen: false,
      changes: [],
      isPending: true,
      handleReimport: mockHandleReimport,
      handleConfirm: mockHandleConfirm,
      handleCancel: mockHandleCancel,
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
