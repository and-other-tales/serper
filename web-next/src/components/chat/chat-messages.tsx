'use client';

import { ReactMarkdown } from 'react-markdown/lib/react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { formatDate } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

type Message = {
  id: string;
  type: 'system' | 'user' | 'assistant' | 'error' | 'thinking';
  content: string;
  timestamp: string;
};

type ChatMessagesProps = {
  messages: Message[];
};

export function ChatMessages({ messages }: ChatMessagesProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center text-center">
        <div className="mb-4 rounded-full bg-primary/10 p-3">
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            className="text-primary"
          >
            <path 
              d="M17 3.33782C15.5291 2.48697 13.8214 2 12 2C6.47715 2 2 6.47715 2 12C2 13.5997 2.37562 15.1116 3.04346 16.4525C3.22094 16.8088 3.28001 17.2161 3.17712 17.6006L2.58151 19.8267C2.32295 20.793 3.20701 21.677 4.17335 21.4185L6.39939 20.8229C6.78393 20.72 7.19121 20.7791 7.54753 20.9565C8.88837 21.6244 10.4003 22 12 22C17.5228 22 22 17.5228 22 12C22 10.1786 21.513 8.47087 20.6622 7" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round"
            />
            <path 
              d="M8 12H16M12 8V16" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round"
            />
          </svg>
        </div>
        <h3 className="mb-1 text-lg font-medium">Welcome to Serper Chat</h3>
        <p className="text-sm text-muted-foreground">
          How can I help you today? You can ask me to create datasets from GitHub repositories<br />
          or websites, manage tasks, or get information about the system.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div 
          key={message.id}
          className={cn(
            "flex items-start gap-3",
            message.type === 'user' && "justify-end"
          )}
        >
          {message.type !== 'user' && (
            <Avatar>
              <AvatarImage src="/serper-logo.png" alt="Serper" />
              <AvatarFallback>AI</AvatarFallback>
            </Avatar>
          )}

          <div 
            className={cn(
              "rounded-lg px-4 py-2 max-w-[80%]",
              message.type === 'user' && "bg-primary text-primary-foreground",
              message.type === 'assistant' && "bg-muted",
              message.type === 'system' && "bg-secondary text-secondary-foreground",
              message.type === 'error' && "bg-destructive text-destructive-foreground",
              message.type === 'thinking' && "bg-muted text-muted-foreground"
            )}
          >
            {message.type === 'thinking' ? (
              <div className="flex items-center">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                <span>{message.content}</span>
              </div>
            ) : message.type === 'user' ? (
              <div>{message.content}</div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={atomDark}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
            <div className="mt-1 text-right text-xs opacity-50">
              {formatDate(message.timestamp)}
            </div>
          </div>

          {message.type === 'user' && (
            <Avatar>
              <AvatarImage src="/user-avatar.png" alt="User" />
              <AvatarFallback>U</AvatarFallback>
            </Avatar>
          )}
        </div>
      ))}
    </div>
  );
}