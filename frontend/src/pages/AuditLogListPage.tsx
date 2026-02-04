import { useState } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Pagination } from '@/components/common/Pagination';
import { useAuditLogs } from '@/hooks';
import type { EventType } from '@/types';

const BADGE_COLORS = {
  success: 'bg-green-500/10 text-green-500 border-green-500/20',
  danger: 'bg-red-500/10 text-red-500 border-red-500/20',
  info: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  warning: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  neutral: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
  caution: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
} as const;

const EVENT_TYPE_LABELS: Record<EventType, { label: string; color: string }> = {
  USER_LOGIN: { label: 'ユーザーログイン', color: BADGE_COLORS.info },
  USER_LOGOUT: { label: 'ユーザーログアウト', color: BADGE_COLORS.neutral },
  USER_LOGIN_FAILED: { label: 'ログイン失敗', color: BADGE_COLORS.danger },
  DASHBOARD_SHARE_ADDED: { label: 'ダッシュボード共有追加', color: BADGE_COLORS.success },
  DASHBOARD_SHARE_REMOVED: { label: 'ダッシュボード共有削除', color: BADGE_COLORS.warning },
  DASHBOARD_SHARE_UPDATED: { label: 'ダッシュボード共有更新', color: BADGE_COLORS.caution },
  DATASET_CREATED: { label: 'データセット作成', color: BADGE_COLORS.success },
  DATASET_IMPORTED: { label: 'データセットインポート', color: BADGE_COLORS.info },
  DATASET_DELETED: { label: 'データセット削除', color: BADGE_COLORS.danger },
  TRANSFORM_EXECUTED: { label: 'Transform実行', color: BADGE_COLORS.success },
  TRANSFORM_FAILED: { label: 'Transform失敗', color: BADGE_COLORS.danger },
  CARD_EXECUTION_FAILED: { label: 'Card実行失敗', color: BADGE_COLORS.danger },
};

const isEventType = (v: string): v is EventType =>
  Object.prototype.hasOwnProperty.call(EVENT_TYPE_LABELS, v);

export function AuditLogListPage() {
  const [offset, setOffset] = useState(0);
  const [eventTypeFilter, setEventTypeFilter] = useState<EventType | undefined>(undefined);
  const limit = 50;

  const { data, isLoading } = useAuditLogs({
    limit,
    offset,
    event_type: eventTypeFilter,
  });

  if (isLoading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">監査ログ</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="w-64">
          <Select
            value={eventTypeFilter || 'all'}
            onValueChange={(value) => {
              setEventTypeFilter(value === 'all' ? undefined : isEventType(value) ? value : undefined);
              setOffset(0);
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="イベントタイプで絞り込み" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">すべて</SelectItem>
              {Object.entries(EVENT_TYPE_LABELS).map(([type, { label }]) => (
                <SelectItem key={type} value={type}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>タイムスタンプ</TableHead>
            <TableHead>イベントタイプ</TableHead>
            <TableHead>ユーザーID</TableHead>
            <TableHead>対象タイプ</TableHead>
            <TableHead>対象ID</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.data.map((log) => {
            const eventInfo = EVENT_TYPE_LABELS[log.event_type] ?? {
              label: log.event_type,
              color: BADGE_COLORS.neutral,
            };
            return (
              <TableRow key={log.log_id}>
                <TableCell className="font-mono text-sm">
                  {new Date(log.timestamp).toLocaleString('ja-JP')}
                </TableCell>
                <TableCell>
                  <Badge className={eventInfo.color}>
                    {eventInfo.label}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-sm">{log.user_id}</TableCell>
                <TableCell>{log.target_type}</TableCell>
                <TableCell className="font-mono text-sm">{log.target_id}</TableCell>
              </TableRow>
            );
          })}
          {data?.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                監査ログがありません
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {data?.pagination && (
        <Pagination
          total={data.pagination.total}
          limit={data.pagination.limit}
          offset={data.pagination.offset}
          onPageChange={setOffset}
        />
      )}
    </div>
  );
}
