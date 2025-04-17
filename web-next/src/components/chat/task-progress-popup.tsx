'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { XCircle, Minimize2, Maximize2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type TaskUpdate = {
  task_id: string;
  progress: number;
  status: string;
  task_type?: string;
};

type TaskProgressPopupProps = {
  task: TaskUpdate;
  onCancel: () => void;
};

export function TaskProgressPopup({ task, onCancel }: TaskProgressPopupProps) {
  const [minimized, setMinimized] = useState(false);
  
  const handleMinimize = () => {
    setMinimized(!minimized);
  };
  
  return (
    <div className={cn(
      "fixed bottom-4 right-4 w-80 rounded-lg border bg-card shadow-lg transition-all",
      minimized && "h-12 w-48"
    )}>
      <div className="flex items-center justify-between border-b p-3">
        <h5 className="text-sm font-medium">Task in Progress</h5>
        <div className="flex items-center gap-1">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={handleMinimize}
            title={minimized ? "Maximize" : "Minimize"}
          >
            {minimized ? (
              <Maximize2 className="h-4 w-4" />
            ) : (
              <Minimize2 className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
      
      {!minimized && (
        <div className="p-4">
          <div className="mb-2 text-xs text-muted-foreground truncate">
            {task.task_type} - {task.task_id}
          </div>
          
          <Progress value={task.progress < 0 ? 100 : task.progress} className={cn(
            task.progress < 0 ? "bg-destructive/20" : "",
            "mb-4"
          )}>
            <div className={cn(
              "h-full w-full transition-all",
              task.progress < 0 ? "bg-destructive" : ""
            )} />
          </Progress>
          
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">
              {task.progress < 0 ? 'Error' : `${Math.round(task.progress)}%`}
            </div>
            <div className="text-sm text-muted-foreground">
              {task.status}
            </div>
          </div>
          
          {task.progress > 0 && task.progress < 100 && (
            <div className="mt-4 flex justify-end">
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={onCancel}
              >
                <XCircle className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}