import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pencil, Filter, Share2, MessageCircle, ChevronRight, LayoutDashboard } from 'lucide-react';
import { FilterViewSelector } from './FilterViewSelector';
import { cn } from '@/lib/utils';
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
    <div className="bg-background border-b pb-4 mb-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
        <Link
          to="/dashboards"
          className="flex items-center gap-1 hover:text-foreground transition-colors"
        >
          <LayoutDashboard className="h-4 w-4" />
          <span>ダッシュボード</span>
        </Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-foreground">{dashboardName}</span>
      </div>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">{dashboardName}</h1>
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
                className={cn(
                  'relative',
                  activeFilterCount > 0 && 'border-primary'
                )}
                title="フィルタ表示切替"
              >
                <Filter className="h-4 w-4" />
                {activeFilterCount > 0 && (
                  <Badge
                    variant="secondary"
                    className="absolute -top-1 -right-1 h-5 min-w-[20px] px-1 text-xs"
                  >
                    {activeFilterCount}
                  </Badge>
                )}
              </Button>
            </>
          )}
          {myPermission !== 'viewer' && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEdit}
              title="編集"
            >
              <Pencil className="h-4 w-4" />
            </Button>
          )}
          {myPermission === 'owner' && (
            <Button
              variant="outline"
              size="sm"
              onClick={onShare}
              title="共有"
            >
              <Share2 className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onChatToggle}
            title="チャット"
          >
            <MessageCircle className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
