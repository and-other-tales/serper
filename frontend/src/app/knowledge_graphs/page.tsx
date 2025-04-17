import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Plus, Eye, Trash2, Database } from 'lucide-react';

export const metadata: Metadata = {
  title: "Knowledge Graphs | Serper",
  description: "Manage Neo4j knowledge graphs",
};

export default function KnowledgeGraphsPage() {
  return (
    <PageLayout title="Knowledge Graphs">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Create New Knowledge Graph</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="md:col-span-2">
                  <Input placeholder="Knowledge Graph Name" />
                </div>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Graph
                </Button>
              </div>
              <div>
                <textarea 
                  className="w-full min-h-[100px] p-2 border rounded-md" 
                  placeholder="Description (optional)"
                ></textarea>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Your Knowledge Graphs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Example graph */}
              <div className="rounded-md border p-4">
                <div className="flex justify-between">
                  <div>
                    <h3 className="text-lg font-medium">example-graph</h3>
                    <p className="text-sm text-muted-foreground">Created: 2023-04-01</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="mr-2 h-4 w-4" />
                      View
                    </Button>
                    <Button variant="destructive" size="sm">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
                <div className="mt-2">
                  <p className="text-sm">Example knowledge graph description.</p>
                </div>
                <div className="mt-2 flex gap-2">
                  <div className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">1,240 nodes</div>
                  <div className="rounded-full bg-green-100 px-2 py-1 text-xs text-green-800">532 relationships</div>
                </div>
              </div>
              
              {/* Empty state */}
              <div className="rounded-md border border-dashed p-8 text-center">
                <p className="text-muted-foreground">No knowledge graphs found. Create one using the form above.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Neo4j Connection</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <label className="text-sm font-medium">Connection URI</label>
                <Input value="bolt://localhost:7687" readOnly />
              </div>
              <div>
                <label className="text-sm font-medium">Status</label>
                <div className="flex items-center mt-2">
                  <div className="h-3 w-3 rounded-full bg-red-500 mr-2"></div>
                  <span className="text-sm">Disconnected</span>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <Button variant="outline">
                <Database className="mr-2 h-4 w-4" />
                Test Connection
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}