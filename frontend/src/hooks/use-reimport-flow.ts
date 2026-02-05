import { useState, useCallback } from 'react';
import { useReimportDryRun, useReimportDataset } from './use-datasets';
import type { SchemaChange } from '@/types/reimport';

interface UseReimportFlowOptions {
  datasetId: string;
}

interface UseReimportFlowReturn {
  dialogOpen: boolean;
  changes: SchemaChange[];
  isPending: boolean;
  handleReimport: () => Promise<void>;
  handleConfirm: () => Promise<void>;
  handleCancel: () => void;
}

/**
 * データセットの再取り込みフローを管理するカスタムフック
 */
export function useReimportFlow({ datasetId }: UseReimportFlowOptions): UseReimportFlowReturn {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [changes, setChanges] = useState<SchemaChange[]>([]);

  const { mutateAsync: dryRunMutateAsync, isPending: isDryRunPending } = useReimportDryRun();
  const { mutateAsync: reimportMutateAsync, isPending: isReimportPending } = useReimportDataset();

  const isPending = isDryRunPending || isReimportPending;

  const handleReimport = useCallback(async () => {
    const result = await dryRunMutateAsync(datasetId);
    if (result.has_schema_changes) {
      setChanges(result.changes);
      setDialogOpen(true);
    } else {
      await reimportMutateAsync({ datasetId, force: false });
    }
  }, [datasetId, dryRunMutateAsync, reimportMutateAsync]);

  const handleConfirm = useCallback(async () => {
    await reimportMutateAsync({ datasetId, force: true });
    setDialogOpen(false);
  }, [datasetId, reimportMutateAsync]);

  const handleCancel = useCallback(() => {
    setDialogOpen(false);
    setChanges([]);
  }, []);

  return {
    dialogOpen,
    changes,
    isPending,
    handleReimport,
    handleConfirm,
    handleCancel,
  };
}
