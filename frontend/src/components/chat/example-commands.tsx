'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

type ExampleCommandProps = {
  command: string;
  description?: string;
  onClick: (command: string) => void;
};

function ExampleCommand({ command, description, onClick }: ExampleCommandProps) {
  return (
    <button
      className="w-full rounded-md bg-muted p-3 text-left hover:bg-muted/80"
      onClick={() => onClick(command)}
    >
      <div className="font-medium">{command}</div>
      {description && <div className="text-xs text-muted-foreground">{description}</div>}
    </button>
  );
}

export function ExampleCommands() {
  const handleCommandClick = (command: string) => {
    // Find the message input and set its value
    const inputElement = document.querySelector('input[placeholder="Type a message..."]') as HTMLInputElement;
    if (inputElement) {
      inputElement.value = command;
      inputElement.focus();
      
      // Trigger input event to update React state
      const event = new Event('input', { bubbles: true });
      inputElement.dispatchEvent(event);
    }
  };

  const examples = [
    {
      title: 'GitHub Datasets',
      commands: [
        {
          command: 'Create a dataset from the GitHub repository langchain-ai/langchain',
          description: 'Generate a dataset from a specific GitHub repository'
        },
        {
          command: 'Create a dataset from the OpenAI organization repositories',
          description: 'Generate a dataset from all repositories in an organization'
        }
      ]
    },
    {
      title: 'Web Crawling',
      commands: [
        {
          command: 'Create a dataset from the React documentation website',
          description: 'Crawl a website to generate a dataset'
        },
        {
          command: 'Create a dataset from https://example.com with recursive crawling',
          description: 'Crawl a website and follow links recursively'
        }
      ]
    },
    {
      title: 'Management',
      commands: [
        {
          command: 'What datasets do I have?',
          description: 'List all your datasets'
        },
        {
          command: 'Show me my recent tasks',
          description: 'View your active and recent tasks'
        },
        {
          command: 'Set up my Hugging Face credentials',
          description: 'Configure your credentials'
        }
      ]
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Example Commands</CardTitle>
        <CardDescription>
          Click on any example to try it out
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-3">
          {examples.map((section, i) => (
            <div key={i} className="space-y-3">
              <h3 className="font-semibold">{section.title}</h3>
              <div className="space-y-2">
                {section.commands.map((cmd, j) => (
                  <ExampleCommand
                    key={j}
                    command={cmd.command}
                    description={cmd.description}
                    onClick={handleCommandClick}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}