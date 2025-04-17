'use client';

import { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { formatDate } from '@/lib/utils';
import { AlertCircle, CheckCircle2, Edit2, MessageSquare, X } from 'lucide-react';

type HumanInLoopTask = {
  id: string;
  action_request: {
    action: string;
    args: Record<string, any>;
  };
  description: string;
  config: {
    allow_ignore: boolean;
    allow_respond: boolean;
    allow_edit: boolean;
    allow_accept: boolean;
  };
  status: string;
  created_at: string;
};

export function AgentInboxDashboard() {
  const [tasks, setTasks] = useState<HumanInLoopTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<HumanInLoopTask | null>(null);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'accept' | 'edit' | 'respond' | null>(null);
  const [responseText, setResponseText] = useState('');
  const [editedArgs, setEditedArgs] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      // In a real app, this would fetch from your API
      // Mock data for demonstration
      const mockTasks: HumanInLoopTask[] = [
        {
          id: 'task_123',
          action_request: {
            action: 'Approve Email',
            args: {
              subject: 'Meeting Tomorrow',
              body: 'Hi team, just a reminder that we have a meeting tomorrow at 10am to discuss the project progress.',
              recipient: 'team@example.com'
            }
          },
          description: 'Please review this email before sending it to the team.',
          config: {
            allow_ignore: true,
            allow_respond: true,
            allow_edit: true,
            allow_accept: true
          },
          status: 'waiting',
          created_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: 'task_456',
          action_request: {
            action: 'Verify Data',
            args: {
              filename: 'quarterly_report.csv',
              rows: 245,
              columns: 15,
              suspicious_entries: 3
            }
          },
          description: 'The system detected some suspicious entries in the quarterly report data. Please verify if they need correction.',
          config: {
            allow_ignore: true,
            allow_respond: true,
            allow_edit: false,
            allow_accept: true
          },
          status: 'waiting',
          created_at: new Date(Date.now() - 7200000).toISOString()
        }
      ];
      
      setTasks(mockTasks);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching human-in-loop tasks:', error);
      setLoading(false);
    }
  };

  const handleTaskAction = (task: HumanInLoopTask, action: 'accept' | 'edit' | 'respond' | 'ignore') => {
    setSelectedTask(task);
    
    if (action === 'ignore') {
      // Handle ignore immediately
      handleSubmitAction('ignore', null);
    } else {
      // For other actions, open the dialog
      setActionType(action);
      
      // Initialize edited args for edit action
      if (action === 'edit') {
        setEditedArgs({...task.action_request.args});
      }
      
      setActionDialogOpen(true);
    }
  };

  const handleSubmitAction = async (
    action: 'accept' | 'edit' | 'respond' | 'ignore', 
    data: any
  ) => {
    if (!selectedTask) return;
    
    setIsSubmitting(true);
    
    try {
      // In a real app, this would send to your API
      console.log('Submitting action:', {
        task_id: selectedTask.id,
        action,
        data
      });
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update tasks list by removing the handled task
      setTasks(tasks.filter(t => t.id !== selectedTask.id));
      
      // Show success message
      const actionMessages = {
        accept: 'Task accepted successfully',
        edit: 'Task edited successfully',
        respond: 'Response submitted successfully',
        ignore: 'Task ignored'
      };
      
      toast.success(actionMessages[action]);
      
      // Reset states
      setSelectedTask(null);
      setActionType(null);
      setResponseText('');
      setEditedArgs({});
      setActionDialogOpen(false);
    } catch (error) {
      console.error('Error submitting action:', error);
      toast.error('Failed to submit action');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Task Management & Human-in-Loop</CardTitle>
          <CardDescription>
            Tasks requiring human intervention will appear here
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" asChild>
          <a href="/tasks">Go to Task Management</a>
        </Button>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
            <span className="ml-2">Loading tasks...</span>
          </div>
        ) : tasks.length > 0 ? (
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.id} className="rounded-lg border p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-medium">{task.action_request.action}</h3>
                  <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-800">
                    Waiting for review
                  </span>
                </div>
                <div className="mb-4">
                  <div className="mb-2 text-sm text-gray-600">
                    Created {formatDate(task.created_at)}
                  </div>
                  <div className="mb-4 rounded-md bg-gray-50 p-3 text-sm">
                    {task.description}
                  </div>
                  <div className="mb-2 font-medium">Arguments:</div>
                  <pre className="mb-4 overflow-auto rounded-md bg-gray-100 p-3 text-xs">
                    {JSON.stringify(task.action_request.args, null, 2)}
                  </pre>
                </div>
                <div className="flex flex-wrap gap-2">
                  {task.config.allow_accept && (
                    <Button 
                      variant="default" 
                      size="sm"
                      onClick={() => handleTaskAction(task, 'accept')}
                    >
                      <CheckCircle2 className="mr-1 h-4 w-4" /> Accept
                    </Button>
                  )}
                  {task.config.allow_edit && (
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleTaskAction(task, 'edit')}
                    >
                      <Edit2 className="mr-1 h-4 w-4" /> Edit
                    </Button>
                  )}
                  {task.config.allow_respond && (
                    <Button 
                      variant="secondary" 
                      size="sm"
                      onClick={() => handleTaskAction(task, 'respond')}
                    >
                      <MessageSquare className="mr-1 h-4 w-4" /> Respond
                    </Button>
                  )}
                  {task.config.allow_ignore && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleTaskAction(task, 'ignore')}
                    >
                      <X className="mr-1 h-4 w-4" /> Ignore
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="mb-2 h-8 w-8 text-muted-foreground" />
            <p className="text-center text-muted-foreground">No tasks requiring human intervention at this time.</p>
          </div>
        )}
      </CardContent>

      {/* Action Dialog */}
      <Dialog open={actionDialogOpen} onOpenChange={setActionDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {actionType === 'accept' ? 'Accept Task' : 
               actionType === 'edit' ? 'Edit Task' : 
               'Respond to Task'}
            </DialogTitle>
          </DialogHeader>
          
          {actionType === 'accept' && selectedTask && (
            <div className="space-y-4">
              <p>Are you sure you want to accept this task with the current arguments?</p>
              <pre className="max-h-60 overflow-auto rounded-md bg-gray-100 p-3 text-xs">
                {JSON.stringify(selectedTask.action_request.args, null, 2)}
              </pre>
            </div>
          )}
          
          {actionType === 'edit' && selectedTask && (
            <div className="space-y-4">
              <p>Edit the arguments before submitting:</p>
              <div className="space-y-4">
                {Object.entries(editedArgs).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <Label htmlFor={`edit-${key}`}>{key}</Label>
                    {typeof value === 'string' && value.length > 50 ? (
                      <Textarea
                        id={`edit-${key}`}
                        value={value}
                        onChange={(e) => setEditedArgs({...editedArgs, [key]: e.target.value})}
                        rows={4}
                      />
                    ) : (
                      <Input
                        id={`edit-${key}`}
                        value={value}
                        onChange={(e) => setEditedArgs({...editedArgs, [key]: e.target.value})}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {actionType === 'respond' && (
            <div className="space-y-4">
              <p>Enter your response:</p>
              <Textarea
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                placeholder="Type your response here..."
                rows={5}
              />
            </div>
          )}
          
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setActionDialogOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button 
              onClick={() => {
                if (actionType === 'accept') {
                  handleSubmitAction('accept', null);
                } else if (actionType === 'edit') {
                  handleSubmitAction('edit', editedArgs);
                } else if (actionType === 'respond') {
                  handleSubmitAction('respond', responseText);
                }
              }}
              disabled={isSubmitting || (actionType === 'respond' && !responseText)}
            >
              {isSubmitting ? (
                <>
                  <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent"></span>
                  Submitting...
                </>
              ) : (
                'Submit'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}