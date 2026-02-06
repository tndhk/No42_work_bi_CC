import { useState, useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
} from '@/components/ui/sheet';
import { LogOut, Menu, LayoutDashboard, Database, Repeat, CreditCard, Users, ScrollText } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useLogout } from '@/hooks';
import { MobileSidebar } from './MobileSidebar';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/dashboards', label: 'DASHBOARDS', icon: LayoutDashboard },
  { to: '/datasets', label: 'DATASETS', icon: Database },
  { to: '/transforms', label: 'TRANSFORMS', icon: Repeat },
  { to: '/cards', label: 'CARDS', icon: CreditCard },
];

const adminNavItems = [
  { to: '/admin/groups', label: 'GROUPS', icon: Users },
  { to: '/admin/audit-logs', label: 'AUDIT LOGS', icon: ScrollText },
];

export function Header() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin';
  const { mutate: logout } = useLogout();
  const { toggle } = useSidebarStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const userInitial = useMemo(() => {
    if (!user?.email) return '?';
    return user.email.charAt(0).toUpperCase();
  }, [user?.email]);

  // Determine which nav items to show based on role
  const visibleNavItems = isAdmin ? [...navItems, ...adminNavItems] : [{ to: '/dashboards', label: 'DASHBOARDS', icon: LayoutDashboard }];

  return (
    <header className="sticky top-0 z-50 w-full shadow-[0_1px_0_0_hsl(var(--border))] bg-header border-b border-header-border">
      <div className="flex h-14 items-center px-4">
        <div className="flex items-center gap-2 md:hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden h-8 w-8 p-0 text-header-foreground hover:bg-header-hover"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        <div className="hidden md:flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggle}
            className="hidden md:flex h-8 w-8 p-0 text-header-foreground hover:bg-header-hover"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        
        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 ml-4">
          {visibleNavItems.map((item) => {
            const isActive = location.pathname === item.to || 
              (item.to !== '/dashboards' && location.pathname.startsWith(item.to));
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200',
                  isActive
                    ? 'bg-header-active text-header-active-foreground'
                    : 'text-header-foreground/80 hover:bg-header-hover hover:text-header-foreground'
                )}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
        
        <div className="ml-auto flex items-center gap-3">
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2.5 h-8 px-2 hover:bg-header-hover text-header-foreground">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-header-active text-header-active-foreground">
                    <span className="text-xs font-semibold">{userInitial}</span>
                  </div>
                  <span className="hidden sm:inline font-mono text-xs text-header-foreground/80">
                    {user.email}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem disabled>
                  <span className="font-mono text-xs">{user.email}</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => logout()}>
                  <LogOut className="mr-2 h-4 w-4" />
                  ログアウト
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <MobileSidebar onNavigate={() => setMobileMenuOpen(false)} />
        </SheetContent>
      </Sheet>
    </header>
  );
}
