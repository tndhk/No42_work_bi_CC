import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { BarChart3, Database, LayoutDashboard, CreditCard, Users, Repeat, ScrollText, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebarStore } from '@/stores/sidebar-store';

const navItems = [
  { to: '/dashboards', label: 'ダッシュボード', icon: LayoutDashboard },
  { to: '/datasets', label: 'データセット', icon: Database },
  { to: '/transforms', label: 'Transform', icon: Repeat },
  { to: '/cards', label: 'カード', icon: CreditCard },
];

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin';
  const { collapsed, toggle } = useSidebarStore();

  const items = [
    ...navItems,
    ...(isAdmin ? [
      { to: '/admin/groups', label: 'グループ管理', icon: Users },
      { to: '/admin/audit-logs', label: '監査ログ', icon: ScrollText },
    ] : []),
  ];

  return (
    <aside
      className={cn(
        'hidden md:flex flex-col bg-sidebar border-r border-border transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      <div className={cn(
        'flex h-14 items-center border-b border-border px-4',
        collapsed && 'justify-center'
      )}>
        <BarChart3 className={cn(
          'h-5 w-5 text-sidebar-active flex-shrink-0',
          collapsed ? '' : 'mr-2'
        )} />
        {!collapsed && (
          <span className="text-foreground font-semibold tracking-tight">BI Tool</span>
        )}
      </div>
      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center rounded-lg text-sm transition-colors relative',
                collapsed ? 'justify-center px-2 py-2' : 'gap-3 px-3 py-2',
                isActive
                  ? 'bg-primary text-sidebar-active-foreground'
                  : 'text-sidebar-foreground hover:bg-muted'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn('h-4 w-4 flex-shrink-0', collapsed && 'mx-auto')} />
                {!collapsed && <span>{item.label}</span>}
                {collapsed && isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-border p-2">
        <button
          onClick={toggle}
          className={cn(
            'flex items-center justify-center w-full rounded-lg p-2 text-sm transition-colors text-sidebar-foreground hover:bg-muted',
            collapsed ? 'px-2' : 'px-3'
          )}
          title={collapsed ? 'サイドバーを展開' : 'サイドバーを折りたたむ'}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span>折りたたむ</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
