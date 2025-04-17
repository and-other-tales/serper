'use client';

import { useState } from 'react';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';

export function NewTaskModal() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('github');
  
  // GitHub form state
  const [githubRepo, setGithubRepo] = useState('');
  const [githubDatasetName, setGithubDatasetName] = useState('');
  const [githubDescription, setGithubDescription] = useState('');
  
  // Web form state
  const [webUrl, setWebUrl] = useState('');
  const [webDatasetName, setWebDatasetName] = useState('');
  const [webDescription, setWebDescription] = useState('');
  const [recursive, setRecursive] = useState(false);
  const [exportGraph, setExportGraph] = useState(true);
  
  // Loading states
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    try {
      if (activeTab === 'github') {
        // Validate GitHub form
        if (!githubRepo || !githubDatasetName) {
          toast.error('Repository URL and Dataset Name are required');
          setIsSubmitting(false);
          return;
        }
        
        // Create GitHub task
        const response = await fetch('/api/tasks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: 'github_repository',
            source: githubRepo,
            dataset_name: githubDatasetName,
            description: githubDescription || `Dataset created from ${githubRepo}`,
          }),
        });
        
        if (response.ok) {
          toast.success('GitHub repository task created successfully');
          setOpen(false);
          resetForms();
        } else {
          const error = await response.json();
          toast.error(`Failed to create task: ${error.message || 'Unknown error'}`);
        }
      } else {
        // Validate Web form
        if (!webUrl || !webDatasetName) {
          toast.error('Website URL and Dataset Name are required');
          setIsSubmitting(false);
          return;
        }
        
        // Create Web task
        const response = await fetch('/api/tasks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: 'web_crawler',
            source: webUrl,
            dataset_name: webDatasetName,
            description: webDescription || `Dataset created from ${webUrl}`,
            recursive: recursive,
            export_to_graph: exportGraph,
          }),
        });
        
        if (response.ok) {
          toast.success('Web crawler task created successfully');
          setOpen(false);
          resetForms();
        } else {
          const error = await response.json();
          toast.error(`Failed to create task: ${error.message || 'Unknown error'}`);
        }
      }
    } catch (error) {
      console.error('Error creating task:', error);
      toast.error('Failed to create task due to an unexpected error');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const resetForms = () => {
    // Reset GitHub form
    setGithubRepo('');
    setGithubDatasetName('');
    setGithubDescription('');
    
    // Reset Web form
    setWebUrl('');
    setWebDatasetName('');
    setWebDescription('');
    setRecursive(false);
    setExportGraph(true);
  };
  
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button id="new-task-trigger" className="hidden">New Task</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
          <DialogDescription>
            Create a new dataset from a GitHub repository or website.
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="github" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="github">GitHub Repository</TabsTrigger>
            <TabsTrigger value="web">Web Crawler</TabsTrigger>
          </TabsList>
          
          <TabsContent value="github" className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="github-repo">GitHub Repository URL</Label>
              <Input 
                id="github-repo" 
                placeholder="https://github.com/username/repo" 
                value={githubRepo}
                onChange={(e) => setGithubRepo(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="github-dataset-name">Dataset Name</Label>
              <Input 
                id="github-dataset-name" 
                placeholder="my-github-dataset" 
                value={githubDatasetName}
                onChange={(e) => setGithubDatasetName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="github-description">Description</Label>
              <Textarea 
                id="github-description" 
                placeholder="Dataset description..." 
                rows={3}
                value={githubDescription}
                onChange={(e) => setGithubDescription(e.target.value)}
              />
            </div>
          </TabsContent>
          
          <TabsContent value="web" className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="web-url">Website URL</Label>
              <Input 
                id="web-url" 
                placeholder="https://example.com" 
                value={webUrl}
                onChange={(e) => setWebUrl(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="web-dataset-name">Dataset Name</Label>
              <Input 
                id="web-dataset-name" 
                placeholder="my-web-dataset" 
                value={webDatasetName}
                onChange={(e) => setWebDatasetName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="web-description">Description</Label>
              <Textarea 
                id="web-description" 
                placeholder="Dataset description..." 
                rows={3}
                value={webDescription}
                onChange={(e) => setWebDescription(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch 
                  id="web-recursive" 
                  checked={recursive}
                  onCheckedChange={setRecursive}
                />
                <Label htmlFor="web-recursive">Crawl recursively</Label>
              </div>
              <p className="text-xs text-muted-foreground">
                When enabled, the crawler will follow links to other pages on the same domain.
              </p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch 
                  id="web-export-graph" 
                  checked={exportGraph}
                  onCheckedChange={setExportGraph}
                />
                <Label htmlFor="web-export-graph">Export to knowledge graph</Label>
              </div>
              <p className="text-xs text-muted-foreground">
                When enabled, the content will be exported to a knowledge graph for advanced querying.
              </p>
            </div>
          </TabsContent>
        </Tabs>
        
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent"></span>
                Creating...
              </>
            ) : (
              'Create Task'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}