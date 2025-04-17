import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Trash2, RefreshCw } from 'lucide-react';

export const metadata: Metadata = {
  title: "Hugging Face | Serper",
  description: "Manage Hugging Face datasets",
};

export default function HuggingFacePage() {
  return (
    <PageLayout title="Hugging Face Datasets">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Your Datasets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Example dataset rows */}
              <div className="rounded-md border p-4">
                <div className="flex justify-between">
                  <div>
                    <h3 className="text-lg font-medium">example-dataset</h3>
                    <p className="text-sm text-muted-foreground">Created: 2023-04-01</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <Button variant="outline" size="sm">
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Update
                    </Button>
                    <Button variant="destructive" size="sm">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
                <div className="mt-2">
                  <p className="text-sm">Example dataset description shows here.</p>
                </div>
                <div className="mt-2 flex gap-2">
                  <div className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">1,240 downloads</div>
                  <div className="rounded-full bg-green-100 px-2 py-1 text-xs text-green-800">32 files</div>
                </div>
              </div>
              
              {/* Empty state */}
              <div className="rounded-md border border-dashed p-8 text-center">
                <p className="text-muted-foreground">No datasets found. Create a dataset using the GitHub or Web Crawler tools.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dataset Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-md bg-muted p-4 text-center">
                <div className="text-2xl font-bold">0</div>
                <div className="text-xs text-muted-foreground">Total Datasets</div>
              </div>
              <div className="rounded-md bg-muted p-4 text-center">
                <div className="text-2xl font-bold">0</div>
                <div className="text-xs text-muted-foreground">Total Files</div>
              </div>
              <div className="rounded-md bg-muted p-4 text-center">
                <div className="text-2xl font-bold">0</div>
                <div className="text-xs text-muted-foreground">Total Downloads</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}