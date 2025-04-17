'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { ChatMessages } from '@/components/chat/chat-messages';
import { TaskProgressPopup } from '@/components/chat/task-progress-popup';

type Message = {
  id: string;
  type: 'system' | 'user' | 'assistant' | 'error' | 'thinking';
  content: string;
  timestamp: string;
};

type TaskUpdate = {
  task_id: string;
  progress: number;
  status: string;
  task_type?: string;
};

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [activeTask, setActiveTask] = useState<TaskUpdate | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Determine WebSocket URL (secure in production, non-secure in dev)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws`;
    
    // Connect to WebSocket
    socketRef.current = new WebSocket(socketUrl);
    
    socketRef.current.onopen = () => {
      setConnected(true);
      setConnecting(false);
    };
    
    socketRef.current.onclose = () => {
      setConnected(false);
      setConnecting(false);
    };
    
    socketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
      setConnecting(false);
      toast.error('Failed to connect to chat server');
    };
    
    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'task_update') {
          // Handle task update
          setActiveTask({
            task_id: data.task_id,
            progress: data.progress,
            status: data.status,
            task_type: data.task_type
          });
          
          // If task completed or failed, clear active task after a delay
          if (data.progress === 100 || data.progress < 0) {
            setTimeout(() => {
              setActiveTask(null);
            }, 5000);
          }
        } else if (data.type === 'remove_message') {
          // Remove a specific message by ID
          setMessages(prev => prev.filter(msg => msg.id !== data.message_id));
        } else if (['system', 'user', 'assistant', 'error', 'thinking'].includes(data.type)) {
          // Add message to chat
          setMessages(prev => [...prev, {
            id: data.id || crypto.randomUUID(),
            type: data.type,
            content: data.content,
            timestamp: data.timestamp || new Date().toISOString()
          }]);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    // Cleanup on unmount
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);
  
  // Scroll to bottom of messages when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!input.trim()) return;
    if (!connected) {
      toast.error('Not connected to chat server');
      return;
    }
    
    // Send message to server
    socketRef.current?.send(input);
    
    // Add user message to chat (server will also echo it back)
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      type: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }]);
    
    // Clear input
    setInput('');
  };
  
  const handleClearChat = () => {
    setMessages([]);
  };
  
  const handleCancelTask = () => {
    if (!activeTask || !socketRef.current) return;
    
    try {
      socketRef.current.send(JSON.stringify({
        type: 'cancel_task',
        task_id: activeTask.task_id
      }));
      
      toast.success('Task cancellation requested');
    } catch (error) {
      console.error('Error cancelling task:', error);
      toast.error('Failed to cancel task');
    }
  };

  return (
    <>
      <Card className="h-[70vh] overflow-hidden">
        <CardContent className="flex h-full flex-col p-0">
          <div className="flex items-center justify-between border-b p-3">
            <div className="flex items-center">
              <h3 className="text-lg font-semibold">Serper AI Assistant</h3>
            </div>
            <div className="flex items-center gap-2">
              <div className="mr-2 flex items-center">
                <div className={`mr-2 h-2 w-2 rounded-full ${connected ? 'bg-green-500' : connecting ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-muted-foreground">
                  {connected ? 'Connected' : connecting ? 'Connecting...' : 'Disconnected'}
                </span>
              </div>
              <Button variant="ghost" size="sm" onClick={handleClearChat}>
                Clear Chat
              </Button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4">
            <ChatMessages messages={messages} />
            <div ref={messagesEndRef} />
          </div>
          
          <div className="border-t p-3">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <Input
                placeholder="Type a message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={!connected}
                className="flex-1"
              />
              <Button type="submit" disabled={!connected || !input.trim()}>
                {connected ? <Send className="h-4 w-4" /> : <Loader2 className="h-4 w-4 animate-spin" />}
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
      
      {activeTask && (
        <TaskProgressPopup
          task={activeTask}
          onCancel={handleCancelTask}
        />
      )}
    </>
  );
}