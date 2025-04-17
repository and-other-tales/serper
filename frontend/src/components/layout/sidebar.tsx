import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  GitBranch,
  Database,
  Network,
  ListTodo,
  Settings,
  MessageSquare,
} from 'lucide-react';

type SidebarProps = {
  className?: string;
};

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const pathname = usePathname();

  const navItems = [
    {
      name: 'Dashboard',
      href: '/',
      icon: LayoutDashboard,
    },
    {
      name: 'Chat',
      href: '/chat',
      icon: MessageSquare,
    },
    {
      name: 'Tasks',
      href: '/tasks',
      icon: ListTodo,
    },
    {
      name: 'GitHub',
      href: '/github',
      icon: GitBranch,
    },
    {
      name: 'Datasets',
      href: '/datasets',
      icon: Database,
    },
    {
      name: 'Knowledge Graphs',
      href: '/knowledge-graphs',
      icon: Network,
    },
    {
      name: 'Configuration',
      href: '/configuration',
      icon: Settings,
    },
  ];

  return (
    <div className={cn('flex h-screen w-64 flex-col bg-slate-800 text-white', className)}>
      <div className="p-6">
        <h1 className="text-2xl font-bold">Serper</h1>
        <p className="text-sm text-slate-400">Dataset Generator</p>
      </div>

      <nav className="flex-1 space-y-1 px-4 py-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:bg-slate-700 hover:text-white'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500"></div>
          <span>Server Status: Online</span>
        </div>
        <div className="mt-1">API Port: 8080</div>
      </div>
    </div>
  );
};

export default Sidebar;