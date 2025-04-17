import PageLayout from "@/components/layout/page-layout";
import { ChatInterface } from "@/components/chat/chat-interface";
import { ExampleCommands } from "@/components/chat/example-commands";

export default function ChatPage() {
  return (
    <PageLayout title="Chat Interface">
      <div className="mx-auto flex max-w-5xl flex-col space-y-4">
        <ChatInterface />
        <ExampleCommands />
      </div>
    </PageLayout>
  );
}