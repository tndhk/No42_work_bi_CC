export interface FilterView {
  id: string;
  dashboard_id: string;
  name: string;
  owner_id: string;
  filter_state: Record<string, unknown>;
  is_shared: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface FilterViewCreateRequest {
  name: string;
  filter_state: Record<string, unknown>;
  is_shared?: boolean;
  is_default?: boolean;
}

export interface FilterViewUpdateRequest {
  name?: string;
  filter_state?: Record<string, unknown>;
  is_shared?: boolean;
  is_default?: boolean;
}

export function isFilterView(value: unknown): value is FilterView {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.dashboard_id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.owner_id === 'string'
  );
}
