import { useState, useCallback } from 'react';
import { updateFilterState } from '@/lib/filter-utils';

/**
 * ダッシュボードのフィルター状態を管理するカスタムフック
 */
export function useDashboardFilters() {
  const [filterValues, setFilterValues] = useState<Record<string, unknown>>({});
  const [selectedViewId, setSelectedViewId] = useState<string | undefined>();

  const handleFilterChange = useCallback((filterId: string, value: unknown) => {
    setFilterValues((prev) => updateFilterState(prev, filterId, value));
  }, []);

  const handleClearAll = useCallback(() => {
    setFilterValues({});
    setSelectedViewId(undefined);
  }, []);

  const setFilters = useCallback((filters: Record<string, unknown>) => {
    setFilterValues(filters);
  }, []);

  const setSelectedView = useCallback((viewId: string | undefined) => {
    setSelectedViewId(viewId);
  }, []);

  return {
    filterValues,
    selectedViewId,
    handleFilterChange,
    handleClearAll,
    setFilters,
    setSelectedView,
  };
}
