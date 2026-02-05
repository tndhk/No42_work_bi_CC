export interface ColumnSchema {
  name: string;
  data_type: string;
  nullable: boolean;
}

export interface Dataset {
  id: string;
  name: string;
  source_type: string;
  row_count: number;
  column_count: number;
  owner_id: string | null;
  created_at: string;
  last_import_at?: string;
}

export interface DatasetDetail extends Dataset {
  source_config?: Record<string, unknown> | null;
  columns: ColumnSchema[];
  s3_path?: string;
  partition_column?: string;
  updated_at: string;
  last_import_by?: string | null;
}

export interface DatasetCreateRequest {
  file: File;
  name: string;
  has_header?: boolean;
  delimiter?: string;
  encoding?: string;
  partition_column?: string;
}

export interface DatasetUpdateRequest {
  name?: string;
  partition_column?: string;
}

export interface S3ImportRequest {
  name: string;
  s3_bucket: string;
  s3_key: string;
  has_header?: boolean;
  delimiter?: string;
  encoding?: string;
  partition_column?: string;
}

export interface DatasetPreview {
  columns: string[];
  rows: unknown[][];
  total_rows: number;
  preview_rows: number;
}

export function isDataset(value: unknown): value is Dataset {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.source_type === 'string' &&
    typeof obj.row_count === 'number'
  );
}

export function isColumnSchema(value: unknown): value is ColumnSchema {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.name === 'string' &&
    typeof obj.data_type === 'string' &&
    typeof obj.nullable === 'boolean'
  );
}
