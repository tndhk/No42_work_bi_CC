import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { BarChart3, Database, LayoutDashboard, CreditCard, Users } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';

const navItems = [
  { to: '/dashboards', label: 'ダッシュボード', icon: LayoutDashboard },
  { to: '/datasets', label: 'データセット', icon: Database },
  { to: '/cards', label: 'カード', icon: CreditCard },
];

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin';

  const items = [
    ...navItems,
    ...(isAdmin ? [{ to: '/admin/groups', label: 'グループ管理', icon: Users }] : []),
  ];

  return (
    <aside className="hidden md:flex w-60 flex-col bg-sidebar border-r border-white/10">
      <div className="flex h-14 items-center border-b border-white/10 px-4">
        <BarChart3 className="h-5 w-5 mr-2 text-sidebar-active" />
        <span className="text-white font-semibold tracking-tight">BI Tool</span>
      </div>
      <nav className="flex-1 space-y-1 p-2">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-sidebar-active text-sidebar-active-foreground shadow-sm'
                  : 'text-sidebar-foreground hover:bg-white/5 hover:text-white'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
