import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, Pause, AlertCircle, CheckCircle, RefreshCw, Clock } from 'lucide-react';

export const metadata: Metadata = {
  title: "Tasks | Serper",
  description: "Manage running and scheduled tasks",
};

export default function TasksPage() {
  return (
    <PageLayout title="Tasks">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Example active task */}
              <div className="rounded-md border p-4">
                <div className="flex justify-between">
                  <div>
                    <div className="flex items-center">
                      <div className="h-2 w-2 rounded-full bg-green-500 mr-2"></div>
                      <h3 className="text-lg font-medium">Scraping https://example.com</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">Started: 5 minutes ago</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Pause className="mr-2 h-4 w-4" />
                      Pause
                    </Button>
                    <Button variant="destructive" size="sm">
                      <AlertCircle className="mr-2 h-4 w-4" />
                      Cancel
                    </Button>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="text-sm mb-1">Progress: 45%</div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: '45%' }}></div>
                  </div>
                </div>
              </div>
              
              {/* Empty state */}
              <div className="rounded-md border border-dashed p-8 text-center">
                <p className="text-muted-foreground">No active tasks. Create a task using the GitHub or Web Crawler tools.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Completed Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Example completed task */}
              <div className="rounded-md border p-4">
                <div className="flex justify-between">
                  <div>
                    <div className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      <h3 className="text-lg font-medium">Created dataset: example-dataset</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">Completed: 2 hours ago</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Run Again
                    </Button>
                  </div>
                </div>
                <div className="mt-2">
                  <p className="text-sm">Successfully created dataset with 42 files.</p>
                </div>
              </div>
              
              {/* Empty state */}
              <div className="rounded-md border border-dashed p-8 text-center">
                <p className="text-muted-foreground">No completed tasks found.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Scheduled Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Example scheduled task */}
              <div className="rounded-md border p-4">
                <div className="flex justify-between">
                  <div>
                    <div className="flex items-center">
                      <Clock className="h-5 w-5 text-blue-500 mr-2" />
                      <h3 className="text-lg font-medium">Update dataset: example-dataset</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">Scheduled: Daily at midnight</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Play className="mr-2 h-4 w-4" />
                      Run Now
                    </Button>
                    <Button variant="destructive" size="sm">
                      <AlertCircle className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
                <div className="mt-2">
                  <p className="text-sm">Next run: Tomorrow at 12:00 AM</p>
                </div>
              </div>
              
              {/* Empty state */}
              <div className="rounded-md border border-dashed p-8 text-center">
                <p className="text-muted-foreground">No scheduled tasks found.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}