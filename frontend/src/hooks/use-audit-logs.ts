import { useQuery } from '@tanstack/react-query';
import { auditLogsApi } from '@/lib/api';
import type { AuditLogListParams } from '@/types';

export function useAuditLogs(params?: AuditLogListParams) {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: () => auditLogsApi.list(params),
  });
}
