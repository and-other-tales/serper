'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Activity, 
  Database, 
  Server, 
  GitBranch, 
  HardDrive, 
  Network 
} from "lucide-react";
import { useEffect, useState } from "react";

type StatusData = {
  server_status: boolean;
  github_status: boolean;
  huggingface_status: boolean;
  neo4j_status: boolean;
  dataset_count: number;
  cache_size: string;
};

export function DashboardCards() {
  const [statusData, setStatusData] = useState<StatusData>({
    server_status: false,
    github_status: false,
    huggingface_status: false,
    neo4j_status: false,
    dataset_count: 0,
    cache_size: '0 MB',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStatusData() {
      try {
        const response = await fetch('/api/status');
        if (response.ok) {
          const data = await response.json();
          setStatusData({
            server_status: data.status === 'running',
            github_status: data.github_status || false,
            huggingface_status: data.huggingface_status || false,
            neo4j_status: data.neo4j_status || false,
            dataset_count: data.dataset_count || 0,
            cache_size: data.cache_size || '0 MB',
          });
        }
      } catch (error) {
        console.error('Error fetching status data:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchStatusData();
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">System Status</CardTitle>
          <Server className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center">
              <div className={`h-2 w-2 rounded-full ${statusData.server_status ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
              <span className="text-sm">Server: {statusData.server_status ? 'Running' : 'Stopped'}</span>
            </div>
            <div className="flex items-center">
              <div className={`h-2 w-2 rounded-full ${statusData.github_status ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
              <span className="text-sm">GitHub API: {statusData.github_status ? 'Connected' : 'Disconnected'}</span>
            </div>
            <div className="flex items-center">
              <div className={`h-2 w-2 rounded-full ${statusData.huggingface_status ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
              <span className="text-sm">Hugging Face: {statusData.huggingface_status ? 'Connected' : 'Disconnected'}</span>
            </div>
            <div className="flex items-center">
              <div className={`h-2 w-2 rounded-full ${statusData.neo4j_status ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
              <span className="text-sm">Neo4j: {statusData.neo4j_status ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Statistics</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-bold">5</span>
              <span className="text-xs text-muted-foreground">Active Tasks</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-2xl font-bold">{statusData.dataset_count}</span>
              <span className="text-xs text-muted-foreground">Datasets</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-2xl font-bold">8080</span>
              <span className="text-xs text-muted-foreground">API Port</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-2xl font-bold">{statusData.cache_size}</span>
              <span className="text-xs text-muted-foreground">Cache Size</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
          <HardDrive className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <a href="/chat" className="flex items-center rounded-md bg-muted p-2 hover:bg-muted/80">
              <div className="mr-2 rounded-md bg-primary p-1">
                <Activity className="h-3 w-3 text-primary-foreground" />
              </div>
              <div>
                <div className="text-sm font-medium">Open Chat Interface</div>
                <div className="text-xs text-muted-foreground">Interact with Serper AI</div>
              </div>
            </a>
            <a href="/tasks" className="flex items-center rounded-md bg-muted p-2 hover:bg-muted/80">
              <div className="mr-2 rounded-md bg-green-500 p-1">
                <Activity className="h-3 w-3 text-white" />
              </div>
              <div>
                <div className="text-sm font-medium">View All Tasks</div>
                <div className="text-xs text-muted-foreground">Manage active and completed tasks</div>
              </div>
            </a>
            <a href="/datasets" className="flex items-center rounded-md bg-muted p-2 hover:bg-muted/80">
              <div className="mr-2 rounded-md bg-yellow-500 p-1">
                <Database className="h-3 w-3 text-white" />
              </div>
              <div>
                <div className="text-sm font-medium">Dataset Dashboard</div>
                <div className="text-xs text-muted-foreground">Browse and manage datasets</div>
              </div>
            </a>
            <a href="/configuration" className="flex items-center rounded-md bg-muted p-2 hover:bg-muted/80">
              <div className="mr-2 rounded-md bg-blue-500 p-1">
                <Server className="h-3 w-3 text-white" />
              </div>
              <div>
                <div className="text-sm font-medium">Configuration</div>
                <div className="text-xs text-muted-foreground">Manage API keys and settings</div>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}