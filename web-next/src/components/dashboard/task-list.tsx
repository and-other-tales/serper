'use client';

import { useEffect, useState } from 'react';
import { 
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Eye,
  XCircle,
  Play,
  AlertCircle,
  Clock,
  CheckCircle2
} from 'lucide-react';
import { formatDate } from '@/lib/utils';

type Task = {
  id: string;
  type: string;
  status: string;
  progress: number;
  description: string;
  created_at: string;
  updated_at: string;
};

export function DashboardTaskList() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTasks() {
      try {
        const response = await fetch('/api/tasks');
        if (response.ok) {
          const data = await response.json();
          setTasks(data.tasks || []);
        }
      } catch (error) {
        console.error('Error fetching tasks:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTasks();
  }, []);

  const handleViewTask = (taskId: string) => {
    console.log('View task:', taskId);
    // Open task details modal
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/cancel`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Update the task list
        setTasks(tasks.map(task => 
          task.id === taskId ? { ...task, status: 'cancelled', progress: -1 } : task
        ));
      }
    } catch (error) {
      console.error('Error cancelling task:', error);
    }
  };

  const handleResumeTask = async (taskId: string) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}/resume`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Update the task list
        setTasks(tasks.map(task => 
          task.id === taskId ? { ...task, status: 'in_progress', progress: task.progress < 0 ? 0 : task.progress } : task
        ));
      }
    } catch (error) {
      console.error('Error resuming task:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800"><CheckCircle2 className="mr-1 h-3 w-3" /> Completed</span>;
      case 'in_progress':
        return <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"><Clock className="mr-1 h-3 w-3" /> In Progress</span>;
      case 'paused':
        return <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800"><AlertCircle className="mr-1 h-3 w-3" /> Paused</span>;
      case 'failed':
      case 'cancelled':
        return <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800"><XCircle className="mr-1 h-3 w-3" /> Failed</span>;
      default:
        return <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">{status}</span>;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Task Management</CardTitle>
          <CardDescription>Manage your active and recent tasks</CardDescription>
        </div>
        <Button size="sm" variant="outline" asChild>
          <a href="/tasks">View All Tasks</a>
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-primary"></div>
            <span className="ml-2">Loading tasks...</span>
          </div>
        ) : tasks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b text-left text-sm font-medium text-muted-foreground">
                  <th className="px-4 py-3">Task ID</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Started</th>
                  <th className="px-4 py-3">Progress</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 5).map((task) => (
                  <tr key={task.id} className="border-b">
                    <td className="px-4 py-3 text-sm">{task.id}</td>
                    <td className="px-4 py-3 text-sm">{task.type}</td>
                    <td className="px-4 py-3 text-sm">{getStatusBadge(task.status)}</td>
                    <td className="px-4 py-3 text-sm">{formatDate(task.created_at)}</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-100">
                        <div 
                          className={`absolute h-full ${task.progress < 0 ? 'bg-red-500' : 'bg-primary'}`}
                          style={{ width: `${task.progress < 0 ? 100 : task.progress}%` }}
                        ></div>
                      </div>
                      <span className="mt-1 text-xs">{task.progress < 0 ? 'Failed' : `${task.progress}%`}</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex space-x-2">
                        <Button 
                          variant="ghost" 
                          size="icon" 
                          onClick={() => handleViewTask(task.id)}
                          title="View Task"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {task.status === 'in_progress' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleCancelTask(task.id)}
                            title="Cancel Task"
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {task.status === 'paused' && (
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleResumeTask(task.id)}
                            title="Resume Task"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="mb-2 h-8 w-8 text-muted-foreground" />
            <p className="text-center text-muted-foreground">No active tasks found. Start a new task to begin processing data.</p>
          </div>
        )}
      </CardContent>
      <CardFooter className="border-t bg-slate-50/50 px-6 py-3">
        <p className="text-xs text-muted-foreground">Tasks are automatically monitored and managed by the system.</p>
      </CardFooter>
    </Card>
  );
}