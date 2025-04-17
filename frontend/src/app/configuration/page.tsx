import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Save } from 'lucide-react';

export const metadata: Metadata = {
  title: "Configuration | Serper",
  description: "Configure Serper settings",
};

export default function ConfigurationPage() {
  return (
    <PageLayout title="Configuration">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">GitHub Personal Access Token</label>
                <div className="flex gap-2">
                  <Input type="password" placeholder="ghp_xxxxxxxxxxxxxxxx" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Create a token with <code>repo</code> scope at{" "}
                  <a href="https://github.com/settings/tokens" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                    GitHub Settings
                  </a>
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Hugging Face API Token</label>
                <div className="flex gap-2">
                  <Input type="password" placeholder="hf_xxxxxxxxxxxxxxxx" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Create a token at{" "}
                  <a href="https://huggingface.co/settings/tokens" className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                    Hugging Face Settings
                  </a>
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Neo4j Connection String</label>
                <div className="flex gap-2">
                  <Input type="text" placeholder="bolt://localhost:7687" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Format: bolt://hostname:port (default: bolt://localhost:7687)
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Neo4j Username</label>
                <div className="flex gap-2">
                  <Input type="text" placeholder="neo4j" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Neo4j Password</label>
                <div className="flex gap-2">
                  <Input type="password" placeholder="Password" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Server Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">API Port</label>
                <div className="flex gap-2">
                  <Input type="number" placeholder="8080" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Default: 8080 (requires restart to take effect)
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Cache Directory</label>
                <div className="flex gap-2">
                  <Input type="text" placeholder="/tmp/serper_cache" />
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}