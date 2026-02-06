import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useReimportFlow } from '@/hooks/use-reimport-flow';
import { createWrapper } from '@/__tests__/helpers/test-utils';
import type { SchemaChange } from '@/types/reimport';

const mockDryRunMutateAsync = vi.fn();
const mockReimportMutateAsync = vi.fn();

vi.mock('@/hooks/use-datasets', () => ({
  useReimportDryRun: () => ({
    mutateAsync: mockDryRunMutateAsync,
    isPending: false,
  }),
  useReimportDataset: () => ({
    mutateAsync: mockReimportMutateAsync,
    isPending: false,
  }),
}));

describe('useReimportFlow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('初期状態ではダイアログが閉じている', () => {
    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    expect(result.current.dialogOpen).toBe(false);
    expect(result.current.changes).toEqual([]);
    expect(result.current.isPending).toBe(false);
  });

  it('スキーマ変更がない場合は直接再取り込みを実行する', async () => {
    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: false,
      changes: [],
    });
    mockReimportMutateAsync.mockResolvedValue({});

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(mockDryRunMutateAsync).toHaveBeenCalledWith('dataset-001');
      expect(mockReimportMutateAsync).toHaveBeenCalledWith({
        datasetId: 'dataset-001',
        force: false,
      });
      expect(result.current.dialogOpen).toBe(false);
    });
  });

  it('スキーマ変更がある場合は確認ダイアログを表示する', async () => {
    const changes: SchemaChange[] = [
      {
        column_name: 'price',
        change_type: 'type_changed',
        old_value: 'int',
        new_value: 'float',
      },
    ];

    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: true,
      changes,
    });

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(mockDryRunMutateAsync).toHaveBeenCalledWith('dataset-001');
      expect(result.current.dialogOpen).toBe(true);
      expect(result.current.changes).toEqual(changes);
      expect(mockReimportMutateAsync).not.toHaveBeenCalled();
    });
  });

  it('handleConfirmで強制再取り込みを実行しダイアログを閉じる', async () => {
    const changes: SchemaChange[] = [
      {
        column_name: 'status',
        change_type: 'column_added',
        new_value: 'string',
      },
    ];

    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: true,
      changes,
    });
    mockReimportMutateAsync.mockResolvedValue({});

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(result.current.dialogOpen).toBe(true);
    });

    await result.current.handleConfirm();

    await waitFor(() => {
      expect(mockReimportMutateAsync).toHaveBeenCalledWith({
        datasetId: 'dataset-001',
        force: true,
      });
      expect(result.current.dialogOpen).toBe(false);
    });
  });

  it('handleCancelでダイアログを閉じ変更をクリアする', async () => {
    const changes: SchemaChange[] = [
      {
        column_name: 'email',
        change_type: 'column_removed',
        old_value: 'string',
      },
    ];

    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: true,
      changes,
    });

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(result.current.dialogOpen).toBe(true);
      expect(result.current.changes).toEqual(changes);
    });

    act(() => {
      result.current.handleCancel();
    });

    expect(result.current.dialogOpen).toBe(false);
    expect(result.current.changes).toEqual([]);
  });

  it('複数のスキーマ変更を表示する', async () => {
    const changes: SchemaChange[] = [
      {
        column_name: 'price',
        change_type: 'type_changed',
        old_value: 'int',
        new_value: 'float',
      },
      {
        column_name: 'status',
        change_type: 'column_added',
        new_value: 'string',
      },
      {
        column_name: 'old_field',
        change_type: 'column_removed',
        old_value: 'string',
      },
    ];

    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: true,
      changes,
    });

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(result.current.dialogOpen).toBe(true);
      expect(result.current.changes).toEqual(changes);
      expect(result.current.changes).toHaveLength(3);
    });
  });

  it('エラー時もダイアログが開かない', async () => {
    mockDryRunMutateAsync.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await expect(result.current.handleReimport()).rejects.toThrow('Network error');

    expect(result.current.dialogOpen).toBe(false);
    expect(result.current.changes).toEqual([]);
  });

  it('連続して再取り込みを実行できる', async () => {
    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: false,
      changes: [],
    });
    mockReimportMutateAsync.mockResolvedValue({});

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-001' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(mockReimportMutateAsync).toHaveBeenCalledTimes(1);
    });

    await result.current.handleReimport();

    await waitFor(() => {
      expect(mockReimportMutateAsync).toHaveBeenCalledTimes(2);
    });
  });

  it('異なるdatasetIdで動作する', async () => {
    mockDryRunMutateAsync.mockResolvedValue({
      has_schema_changes: false,
      changes: [],
    });
    mockReimportMutateAsync.mockResolvedValue({});

    const { result } = renderHook(
      () => useReimportFlow({ datasetId: 'dataset-002' }),
      { wrapper: createWrapper() }
    );

    await result.current.handleReimport();

    await waitFor(() => {
      expect(mockDryRunMutateAsync).toHaveBeenCalledWith('dataset-002');
      expect(mockReimportMutateAsync).toHaveBeenCalledWith({
        datasetId: 'dataset-002',
        force: false,
      });
    });
  });
});
