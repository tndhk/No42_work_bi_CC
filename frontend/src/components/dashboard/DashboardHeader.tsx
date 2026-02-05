import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pencil, Filter, Share2, MessageCircle } from 'lucide-react';
import { FilterViewSelector } from './FilterViewSelector';
import type { FilterView } from '@/types';

interface DashboardHeaderProps {
  dashboardName: string;
  filterViews: FilterView[];
  selectedViewId?: string;
  activeFilterCount: number;
  filterBarVisible: boolean;
  myPermission?: 'owner' | 'editor' | 'viewer';
  hasFilters: boolean;
  dashboardId: string;
  onToggleFilterBar: () => void;
  onSelectView: (view: FilterView) => void;
  onSaveView: (name: string, options?: { is_shared: boolean }) => void | Promise<void>;
  onOverwriteView: (viewId: string) => void | Promise<void>;
  onDeleteView: (viewId: string) => void | Promise<void>;
  onEdit: () => void;
  onShare: () => void;
  onChatToggle: () => void;
}

export function DashboardHeader({
  dashboardName,
  filterViews,
  selectedViewId,
  activeFilterCount,
  filterBarVisible,
  myPermission,
  hasFilters,
  dashboardId,
  onToggleFilterBar,
  onSelectView,
  onSaveView,
  onOverwriteView,
  onDeleteView,
  onEdit,
  onShare,
  onChatToggle,
}: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <h1 className="text-2xl font-bold">{dashboardName}</h1>
      <div className="flex items-center gap-2">
        {hasFilters && (
          <>
            <FilterViewSelector
              views={filterViews}
              selectedViewId={selectedViewId}
              onSelect={onSelectView}
              onSave={onSaveView}
              onOverwrite={onOverwriteView}
              onDelete={onDeleteView}
              permission={myPermission?.toUpperCase() as 'OWNER' | 'EDITOR' | 'VIEWER'}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleFilterBar}
              aria-label="フィルタ表示切替"
            >
              <Filter className="h-4 w-4 mr-2" />
              フィルタ
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 min-w-[20px] px-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          </>
        )}
        {myPermission !== 'viewer' && (
          <Button variant="outline" onClick={onEdit}>
            <Pencil className="h-4 w-4 mr-2" />
            編集
          </Button>
        )}
        {myPermission === 'owner' && (
          <Button variant="outline" onClick={onShare}>
            <Share2 className="h-4 w-4 mr-2" />
            共有
          </Button>
        )}
        <Button variant="outline" onClick={onChatToggle}>
          <MessageCircle className="h-4 w-4 mr-2" />
          チャット
        </Button>
      </div>
    </div>
  );
}
