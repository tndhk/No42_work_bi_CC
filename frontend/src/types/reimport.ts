export type SchemaChangeType = 'added' | 'removed' | 'type_changed' | 'nullable_changed';

export interface SchemaChange {
  column_name: string;
  change_type: SchemaChangeType;
  old_value: string | null;
  new_value: string | null;
}

export interface ReimportDryRunResponse {
  has_schema_changes: boolean;
  changes: SchemaChange[];
  new_row_count: number;
  new_column_count: number;
}

export interface ReimportRequest {
  force?: boolean;
}

export function isSchemaChange(value: unknown): value is SchemaChange {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.column_name === 'string' &&
    typeof obj.change_type === 'string' &&
    ['added', 'removed', 'type_changed', 'nullable_changed'].includes(obj.change_type as string)
  );
}

export function isReimportDryRunResponse(value: unknown): value is ReimportDryRunResponse {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.has_schema_changes === 'boolean' &&
    Array.isArray(obj.changes) &&
    typeof obj.new_row_count === 'number' &&
    typeof obj.new_column_count === 'number'
  );
}
