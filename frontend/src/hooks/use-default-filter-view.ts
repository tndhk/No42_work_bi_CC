import { useEffect, useRef } from 'react';
import { getDefaultFilterView } from './use-filter-views';
import type { FilterView } from '@/types';

interface UseDefaultFilterViewOptions {
  filterViews: FilterView[];
  currentUserId: string | undefined;
  onApply: (view: FilterView) => void;
}

/**
 * デフォルトフィルタービューを自動適用するカスタムフック
 * 初回のみ実行される
 */
export function useDefaultFilterView({
  filterViews,
  currentUserId,
  onApply,
}: UseDefaultFilterViewOptions) {
  const defaultViewAppliedRef = useRef(false);

  useEffect(() => {
    if (defaultViewAppliedRef.current || !filterViews.length) return;

    const defaultView = getDefaultFilterView(filterViews, currentUserId);
    if (defaultView) {
      onApply(defaultView);
      defaultViewAppliedRef.current = true;
    }
  }, [filterViews, currentUserId, onApply]);
}
