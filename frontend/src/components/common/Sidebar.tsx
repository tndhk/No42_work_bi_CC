import { useState, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { BarChart3, ChevronLeft, ChevronRight, Search, LayoutDashboard } from 'lucide-react';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useDashboards } from '@/hooks/use-dashboards';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export function Sidebar() {
  const { collapsed, toggle } = useSidebarStore();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  
  // Get all dashboards (backend max is 100)
  const { data: dashboardsData, isLoading } = useDashboards({ limit: 100 });
  
  // Extract current dashboard ID from route
  const currentDashboardId = useMemo(() => {
    const match = location.pathname.match(/^\/dashboards\/([^/]+)$/);
    return match ? match[1] : null;
  }, [location.pathname]);
  
  // Filter dashboards by search query
  const filteredDashboards = useMemo(() => {
    if (!dashboardsData?.data) return [];
    if (!searchQuery.trim()) return dashboardsData.data;
    
    const query = searchQuery.toLowerCase();
    return dashboardsData.data.filter((dashboard) =>
      dashboard.name.toLowerCase().includes(query)
    );
  }, [dashboardsData?.data, searchQuery]);

  return (
    <aside
      className={cn(
        'hidden md:flex flex-col bg-sidebar shadow-[1px_0_0_0_hsl(210_12%_18%)] transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <div className={cn(
        'flex h-14 items-center px-4',
        collapsed && 'justify-center'
      )}>
        <BarChart3 className={cn(
          'h-5 w-5 text-sidebar-active flex-shrink-0',
          collapsed ? '' : 'mr-2.5'
        )} />
        {!collapsed && (
          <span className="font-mono text-sm font-semibold uppercase tracking-widest text-sidebar-active">
            BI Tool
          </span>
        )}
      </div>
      
      {!collapsed && (
        <div className="px-3 pt-3 pb-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/70 mb-2 px-1">
            Dashboards
          </h2>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-sidebar-foreground/50" />
            <Input
              type="text"
              placeholder="Filter by name"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 pl-8 pr-2 text-sm bg-sidebar border-sidebar-foreground/20 focus-visible:border-sidebar-active"
            />
          </div>
        </div>
      )}
      
      <nav className="flex-1 overflow-y-auto px-3 pb-3">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="sm" />
          </div>
        ) : filteredDashboards.length === 0 ? (
          <div className="text-center py-8 text-sidebar-foreground/50 text-sm">
            {searchQuery ? 'No dashboards found' : 'No dashboards'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredDashboards.map((dashboard) => {
              const isActive = dashboard.dashboard_id === currentDashboardId;
              return (
                <Link
                  key={dashboard.dashboard_id}
                  to={`/dashboards/${dashboard.dashboard_id}`}
                  title={collapsed ? dashboard.name : undefined}
                  className={cn(
                    'group flex items-center rounded-md text-sm transition-all duration-200 relative',
                    collapsed ? 'justify-center px-2 py-2' : 'gap-2 px-2 py-1.5',
                    isActive
                      ? 'bg-white/[0.08] text-sidebar-active border-l-2 border-sidebar-active'
                      : 'text-sidebar-foreground hover:bg-white/5 hover:text-sidebar-active border-l-2 border-transparent'
                  )}
                >
                  {collapsed ? (
                    <LayoutDashboard className={cn(
                      'h-4 w-4 flex-shrink-0 transition-colors duration-200',
                      isActive ? 'text-sidebar-active' : 'text-sidebar-foreground/70 group-hover:text-sidebar-active'
                    )} />
                  ) : (
                    <>
                      <LayoutDashboard className={cn(
                        'h-4 w-4 flex-shrink-0 transition-colors duration-200',
                        isActive ? 'text-sidebar-active' : 'text-sidebar-foreground/70 group-hover:text-sidebar-active'
                      )} />
                      <span className="flex-1 truncate text-sm">
                        {dashboard.name}
                      </span>
                    </>
                  )}
                  {collapsed && isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-sidebar-active rounded-r-full" />
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </nav>
      
      <div className="p-3">
        <button
          onClick={toggle}
          className={cn(
            'flex items-center justify-center w-full rounded-md p-2 text-sidebar-foreground/50 transition-all duration-200 hover:text-sidebar-foreground hover:bg-white/5',
            collapsed ? 'px-2' : 'px-3'
          )}
          title={collapsed ? 'サイドバーを展開' : 'サイドバーを折りたたむ'}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-xs">折りたたむ</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
