import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { BarChart3, Database, LayoutDashboard, CreditCard, Users, Repeat, ScrollText } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';

const navItems = [
  { to: '/dashboards', label: 'ダッシュボード', icon: LayoutDashboard },
  { to: '/datasets', label: 'データセット', icon: Database },
  { to: '/transforms', label: 'Transform', icon: Repeat },
  { to: '/cards', label: 'カード', icon: CreditCard },
];

interface MobileSidebarProps {
  onNavigate?: () => void;
}

export function MobileSidebar({ onNavigate }: MobileSidebarProps) {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin';

  const items = [
    ...navItems,
    ...(isAdmin ? [
      { to: '/admin/groups', label: 'グループ管理', icon: Users },
      { to: '/admin/audit-logs', label: '監査ログ', icon: ScrollText },
    ] : []),
  ];

  return (
    <div className="flex flex-col h-full bg-sidebar">
      <div className="flex h-14 items-center px-4">
        <BarChart3 className="h-5 w-5 mr-2.5 text-sidebar-active" />
        <span className="font-mono text-sm font-semibold uppercase tracking-widest text-sidebar-active">
          BI Tool
        </span>
      </div>
      <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-all duration-200',
                isActive
                  ? 'bg-white/[0.08] text-sidebar-active border-l-2 border-sidebar-active'
                  : 'text-sidebar-foreground hover:bg-white/5 hover:text-sidebar-active border-l-2 border-transparent'
              )
            }
          >
            <item.icon className="h-4 w-4 transition-colors duration-200 group-hover:text-sidebar-active" />
            <span className="transition-transform duration-200 group-hover:translate-x-0.5">
              {item.label}
            </span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
