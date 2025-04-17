import { Metadata } from "next";
import PageLayout from "@/components/layout/page-layout";
import { NewTaskModal } from "@/components/dashboard/new-task-modal";
import { DashboardCards } from "@/components/dashboard/dashboard-cards";
import { DashboardTaskList } from "@/components/dashboard/task-list";
import { AgentInboxDashboard } from "@/components/dashboard/agent-inbox-dashboard";
import { useState } from "react";

export const metadata: Metadata = {
  title: "Dashboard | Serper",
  description: "Serper Dashboard",
};

export default function DashboardPage() {
  return (
    <PageLayout 
      title="Dashboard" 
      showNewTaskButton={true}
      onNewTask={() => {
        // Open new task modal
        const modalElement = document.getElementById('new-task-modal');
        if (modalElement) {
          const modal = new (window as any).bootstrap.Modal(modalElement);
          modal.show();
        }
      }}
    >
      <div className="space-y-6">
        <DashboardCards />
        <DashboardTaskList />
        <AgentInboxDashboard />
      </div>
      <NewTaskModal />
    </PageLayout>
  );
}