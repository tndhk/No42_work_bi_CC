import type { OwnerRef } from './dataset';

export interface Transform {
  id: string;
  name: string;
  owner_id: string;
  input_dataset_ids: string[];
  output_dataset_id?: string;
  schedule_cron?: string;
  schedule_enabled?: boolean;
  code: string;
  owner: OwnerRef;
  created_at: string;
  updated_at: string;
}

export interface TransformCreateRequest {
  name: string;
  input_dataset_ids: string[];
  code: string;
  schedule_cron?: string;
  schedule_enabled?: boolean;
}

export interface TransformUpdateRequest {
  name?: string;
  input_dataset_ids?: string[];
  code?: string;
  schedule_cron?: string;
  schedule_enabled?: boolean;
}

export interface TransformExecuteResponse {
  execution_id: string;
  output_dataset_id: string;
  row_count: number;
  column_names: string[];
  execution_time_ms: number;
}

export interface TransformExecution {
  execution_id: string;
  transform_id: string;
  status: 'running' | 'success' | 'failed';
  started_at: string;
  finished_at?: string;
  duration_ms?: number;
  output_row_count?: number;
  output_dataset_id?: string;
  error?: string;
  triggered_by: 'manual' | 'schedule';
}

export function isTransform(value: unknown): value is Transform {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.created_at === 'string'
  );
}
