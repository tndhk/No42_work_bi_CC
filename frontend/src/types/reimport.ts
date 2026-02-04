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

