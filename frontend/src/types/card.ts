export interface CardRef {
  id: string;
  name: string;
}

export interface OwnerRef {
  user_id: string;
  name: string;
}

export interface Card {
  card_id?: string;
  id?: string;
  name: string;
  dataset?: CardRef;
  used_columns?: string[];
  filter_applicable?: string[];
  owner?: OwnerRef;
  owner_id?: string;
  card_type?: 'code' | 'text';
  created_at: string;
}

export interface CardDetail extends Card {
  code: string;
  params?: Record<string, unknown>;
  description?: string;
  updated_at: string;
}

export interface CardCreateRequest {
  name: string;
  dataset_id?: string;
  code: string;
  params?: Record<string, unknown>;
  card_type?: 'code' | 'text';
}

export interface CardUpdateRequest {
  name?: string;
  code?: string;
  params?: Record<string, unknown>;
  card_type?: 'code' | 'text';
}

export interface CardExecuteRequest {
  filters?: Record<string, unknown>;
  use_cache?: boolean;
}

export interface CardExecuteResponse {
  card_id: string;
  html: string;
  cached: boolean;
  execution_time_ms: number;
}

export interface CardPreviewResponse {
  card_id: string;
  html: string;
  execution_time_ms: number;
  input_row_count: number;
  filtered_row_count: number;
}

export function isCard(value: unknown): value is Card {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    (typeof obj.card_id === 'string' || typeof obj.id === 'string') &&
    typeof obj.name === 'string' &&
    typeof obj.created_at === 'string'
  );
}
