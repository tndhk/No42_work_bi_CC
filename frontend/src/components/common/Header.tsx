import { useState, useMemo } from 'react';
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
import { LogOut, Menu } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { useSidebarStore } from '@/stores/sidebar-store';
import { useLogout } from '@/hooks';
import { MobileSidebar } from './MobileSidebar';

export function Header() {
  const user = useAuthStore((s) => s.user);
  const { mutate: logout } = useLogout();
  const { toggle } = useSidebarStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const userInitial = useMemo(() => {
    if (!user?.email) return '?';
    return user.email.charAt(0).toUpperCase();
  }, [user?.email]);

  return (
    <header className="sticky top-0 z-50 w-full shadow-[0_1px_0_0_hsl(var(--border))] bg-background/95 backdrop-blur-lg supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-12 items-center px-4">
        <div className="flex items-center gap-2 md:hidden">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden h-8 w-8 p-0"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        <div className="hidden md:flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggle}
            className="hidden md:flex h-8 w-8 p-0"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2.5 h-8 px-2 hover:bg-transparent hover:opacity-80">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 text-primary">
                    <span className="text-xs font-semibold">{userInitial}</span>
                  </div>
                  <span className="hidden sm:inline font-mono text-xs text-muted-foreground">
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
