import type { OwnerRef } from './dataset';

export interface LayoutItem {
  card_id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface FilterDefinition {
  id: string;
  type: 'category' | 'date_range';
  column: string;
  label: string;
  multi_select?: boolean;
}

export interface DashboardLayout {
  cards: LayoutItem[];
  columns: number;
  row_height: number;
}

export interface Dashboard {
  dashboard_id: string;
  name: string;
  card_count: number;
  owner: OwnerRef;
  my_permission?: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardDetail extends Omit<Dashboard, 'card_count'> {
  layout: DashboardLayout;
  filters: FilterDefinition[];
  default_filter_view_id?: string;
  description?: string;
}

export interface DashboardCreateRequest {
  name: string;
}

export interface DashboardUpdateRequest {
  name?: string;
  layout?: DashboardLayout;
  filters?: FilterDefinition[];
}

export function isDashboard(value: unknown): value is Dashboard {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.dashboard_id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.created_at === 'string'
  );
}

export function isLayoutItem(value: unknown): value is LayoutItem {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.card_id === 'string' &&
    typeof obj.x === 'number' &&
    typeof obj.y === 'number' &&
    typeof obj.w === 'number' &&
    typeof obj.h === 'number'
  );
}
