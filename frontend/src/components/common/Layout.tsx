import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden transition-all duration-300">
        <Header />
        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-[1440px] p-6 lg:p-8 xl:p-10 animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
