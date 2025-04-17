import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PlusCircle, Menu } from 'lucide-react';

type HeaderProps = {
  title: string;
  showNewTaskButton?: boolean;
  onNewTask?: () => void;
  onToggleSidebar?: () => void;
  className?: string;
};

const Header: React.FC<HeaderProps> = ({
  title,
  showNewTaskButton = false,
  onNewTask,
  onToggleSidebar,
  className,
}) => {
  return (
    <header className={cn('flex items-center justify-between border-b p-4', className)}>
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="md:hidden"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>
      <div className="flex items-center gap-2">
        {showNewTaskButton && (
          <Button onClick={onNewTask} size="sm">
            <PlusCircle className="mr-2 h-4 w-4" />
            New Task
          </Button>
        )}
      </div>
    </header>
  );
};

export default Header;