'use client';

import React, { useState } from 'react';
import Sidebar from '@/components/layout/sidebar';
import Header from '@/components/layout/header';
import { cn } from '@/lib/utils';

type PageLayoutProps = {
  children: React.ReactNode;
  title: string;
  showNewTaskButton?: boolean;
  onNewTask?: () => void;
};

const PageLayout: React.FC<PageLayoutProps> = ({
  children,
  title,
  showNewTaskButton,
  onNewTask,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar className={cn('hidden md:flex', sidebarOpen ? 'w-64' : 'w-0')} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header 
          title={title} 
          showNewTaskButton={showNewTaskButton} 
          onNewTask={onNewTask}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} 
        />
        <main className="flex-1 overflow-y-auto p-4">{children}</main>
      </div>
    </div>
  );
};

export default PageLayout;