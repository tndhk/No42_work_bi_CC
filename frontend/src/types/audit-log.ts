import type { PaginationParams } from './api';

export type EventType =
  | 'USER_LOGIN' | 'USER_LOGOUT' | 'USER_LOGIN_FAILED'
  | 'DASHBOARD_SHARE_ADDED' | 'DASHBOARD_SHARE_REMOVED' | 'DASHBOARD_SHARE_UPDATED'
  | 'DATASET_CREATED' | 'DATASET_IMPORTED' | 'DATASET_DELETED'
  | 'TRANSFORM_EXECUTED' | 'TRANSFORM_FAILED'
  | 'CARD_EXECUTION_FAILED';

export interface AuditLog {
  log_id: string;
  timestamp: string;   // ISO 8601
  event_type: EventType;
  user_id: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown>;
  request_id: string | null;
}

export interface AuditLogListParams extends PaginationParams {
  event_type?: EventType;
  user_id?: string;
  target_id?: string;
  start_date?: string;
  end_date?: string;
}
