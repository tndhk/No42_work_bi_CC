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
      <div className="flex h-14 items-center border-b border-border px-4">
        <BarChart3 className="h-5 w-5 mr-2 text-sidebar-active" />
        <span className="text-foreground font-semibold tracking-tight">BI Tool</span>
      </div>
      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-primary text-sidebar-active-foreground'
                  : 'text-sidebar-foreground hover:bg-muted'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
