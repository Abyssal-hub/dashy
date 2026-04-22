import { useModules } from "@/hooks/useModules";
import { useDashboardStore } from "@/stores/dashboardStore";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DashboardGrid } from "@/components/layout/DashboardGrid";
import { LogViewer } from "@/components/modules/LogViewer";
import { Button } from "@/components/ui/button";
import { LayoutGrid, Plus, Lock, Unlock } from "lucide-react";

export function DashboardPage() {
  const { data, isLoading } = useModules();
  const { isEditMode, toggleEditMode } = useDashboardStore();
  const modules = data?.modules ?? [];

  return (
    <div className="flex h-screen bg-dark-950">
      <Sidebar activeItem="dashboard" />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Dashboard" />

        {/* Toolbar */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-dark-700 bg-dark-900/50">
          <div className="flex items-center gap-2">
            <Button
              variant={isEditMode ? "default" : "outline"}
              size="sm"
              onClick={toggleEditMode}
              className="gap-2"
            >
              {isEditMode ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
              {isEditMode ? "Done Editing" : "Edit Layout"}
            </Button>
            {isEditMode && (
              <span className="text-xs text-gray-500">Drag and resize modules</span>
            )}
          </div>

          <Button variant="outline" size="sm" className="gap-2">
            <Plus className="w-4 h-4" />
            Add Module
          </Button>
        </div>

        {/* Grid */}
        <main className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
            </div>
          ) : modules.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <LayoutGrid className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">No modules configured</p>
              <p className="text-sm mt-1">Add your first monitoring module</p>
            </div>
          ) : (
            <DashboardGrid modules={modules} />
          )}
        </main>
      </div>
    </div>
  );
}

export function LogsPage() {
  return (
    <div className="flex h-screen bg-dark-950">
      <Sidebar activeItem="logs" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="System Logs" />
        <main className="flex-1 overflow-hidden">
          <LogViewer />
        </main>
      </div>
    </div>
  );
}
