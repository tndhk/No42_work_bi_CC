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
      <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              cn(
                'group flex items-center rounded-md text-sm transition-all duration-200 relative',
                collapsed ? 'justify-center px-2 py-2' : 'gap-3 px-3 py-2',
                isActive
                  ? 'bg-white/[0.08] text-sidebar-active border-l-2 border-sidebar-active'
                  : 'text-sidebar-foreground hover:bg-white/5 hover:text-sidebar-active border-l-2 border-transparent'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn(
                  'h-4 w-4 flex-shrink-0 transition-colors duration-200',
                  collapsed && 'mx-auto',
                  isActive ? 'text-sidebar-active' : 'group-hover:text-sidebar-active'
                )} />
                {!collapsed && (
                  <span className="transition-transform duration-200 group-hover:translate-x-0.5">
                    {item.label}
                  </span>
                )}
                {collapsed && isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-sidebar-active rounded-r-full" />
                )}
              </>
            )}
          </NavLink>
        ))}
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
