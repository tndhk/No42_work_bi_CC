/**
 * フィルター状態更新のユーティリティ関数
 */

/**
 * フィルター状態を更新する
 * value が undefined の場合はフィルターを削除
 */
export function updateFilterState(
  prev: Record<string, unknown>,
  filterId: string,
  value: unknown
): Record<string, unknown> {
  if (value === undefined) {
    const { [filterId]: _, ...rest } = prev;
    return rest;
  }
  return { ...prev, [filterId]: value };
}
