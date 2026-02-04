import { apiClient } from '@/lib/api-client';
import type {
  PaginatedResponse,
  AuditLog,
  AuditLogListParams,
} from '@/types';

export const auditLogsApi = {
  list: async (params?: AuditLogListParams): Promise<PaginatedResponse<AuditLog>> => {
    const searchParams = new URLSearchParams();
    if (params?.event_type) searchParams.set('event_type', params.event_type);
    if (params?.user_id) searchParams.set('user_id', params.user_id);
    if (params?.target_id) searchParams.set('target_id', params.target_id);
    if (params?.start_date) searchParams.set('start_date', params.start_date);
    if (params?.end_date) searchParams.set('end_date', params.end_date);
    if (params?.limit != null) searchParams.set('limit', String(params.limit));
    if (params?.offset != null) searchParams.set('offset', String(params.offset));
    return apiClient.get('audit-logs', { searchParams }).json<PaginatedResponse<AuditLog>>();
  },
};
