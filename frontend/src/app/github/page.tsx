import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, GitFork, GitBranch, Star } from 'lucide-react';

export const metadata: Metadata = {
  title: "GitHub Integration | Serper",
  description: "Connect to GitHub repositories",
};

export default function GitHubPage() {
  return (
    <PageLayout title="GitHub Integration">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Repository Scraper</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input placeholder="Enter GitHub repository URL (e.g., https://github.com/username/repo)" className="flex-1" />
                <Button>
                  <Search className="mr-2 h-4 w-4" />
                  Fetch Repository
                </Button>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GitFork className="h-4 w-4" />
                <span>Fork count will appear here</span>
                
                <GitBranch className="ml-4 h-4 w-4" />
                <span>Branch count will appear here</span>
                
                <Star className="ml-4 h-4 w-4" />
                <span>Star count will appear here</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Repository History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              No repositories have been processed yet.
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization Scraper</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input placeholder="Enter GitHub organization name (e.g., microsoft)" className="flex-1" />
                <Button>
                  <Search className="mr-2 h-4 w-4" />
                  Fetch Organization
                </Button>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Enter an organization name to fetch all public repositories.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}