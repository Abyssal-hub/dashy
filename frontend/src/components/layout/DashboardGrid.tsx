import { useCallback, useEffect, useRef } from "react";
import { Responsive, WidthProvider } from "react-grid-layout";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";
import { useModuleData } from "@/hooks/useModuleData";
import { useDashboardStore } from "@/stores/dashboardStore";
import { updateModuleLayout } from "@/lib/api";
import { GRID_CONFIG } from "@/lib/constants";
import { cn, timeAgo } from "@/lib/utils";
import type { Module, GridLayoutItem } from "@/types";

const ResponsiveGridLayout = WidthProvider(Responsive);

// Module renderer registry — only log module was in scope per spec
const ModuleRenderers: Record<string, React.FC<{ module: Module; data?: Record<string, unknown>; isLoading: boolean }>> = {
  log: LogRenderer,
};

function FallbackRenderer() {
  return <div className="text-gray-500 text-sm">Module type not yet implemented</div>;
}

function LogRenderer({ data, isLoading }: { module: Module; data?: Record<string, unknown>; isLoading: boolean }) {
  if (isLoading) return <LoadingState />;
  const logs = (data?.logs as Array<Record<string, unknown>>) || [];
  return (
    <div className="space-y-1 max-h-40 overflow-auto">
      {logs.slice(0, 6).map((log, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className={cn(
            "px-1.5 py-0.5 rounded",
            log.severity === "ERROR" ? "bg-red-500/20 text-red-400" :
            log.severity === "WARN" ? "bg-amber-500/20 text-amber-400" :
            "bg-blue-500/20 text-blue-400"
          )}>
            {log.severity as string}
          </span>
          <span className="text-gray-400 truncate">{log.message as string}</span>
        </div>
      ))}
      {logs.length === 0 && <p className="text-gray-500 text-sm">No logs</p>}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex items-center justify-center h-24">
      <div className="w-6 h-6 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

interface ModuleCardProps {
  module: Module;
}

function ModuleCard({ module }: ModuleCardProps) {
  const { data, isLoading } = useModuleData(module.id, module.size);
  const Renderer = ModuleRenderers[module.module_type] || FallbackRenderer;
  const dataRecord = data?.data as Record<string, unknown> | undefined;
  const metaRecord = dataRecord?.meta as Record<string, unknown> | undefined;
  const lastUpdated = (dataRecord?.last_updated ?? metaRecord?.last_updated) as string;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className="font-semibold text-white text-sm">{module.name}</h3>
        {lastUpdated && (
          <span className={cn(
            "text-xs",
            new Date().getTime() - new Date(lastUpdated).getTime() < 15 * 60 * 1000
              ? "text-status-online"
              : new Date().getTime() - new Date(lastUpdated).getTime() < 60 * 60 * 1000
              ? "text-status-warning"
              : "text-status-critical"
          )}>
            {timeAgo(lastUpdated)}
          </span>
        )}
      </div>
      <div className="flex-1 overflow-hidden">
        <Renderer module={module} data={data?.data as Record<string, unknown>} isLoading={isLoading} />
      </div>
    </div>
  );
}

interface DashboardGridProps {
  modules: Module[];
}

export function DashboardGrid({ modules }: DashboardGridProps) {
  const { layout, setLayout, isEditMode } = useDashboardStore();
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Convert modules to grid layout items
  useEffect(() => {
    const newLayout: GridLayoutItem[] = modules.map((m) => ({
      i: m.id,
      x: m.position_x ?? 0,
      y: m.position_y ?? 0,
      w: m.width ?? 2,
      h: m.height ?? 2,
    }));
    setLayout(newLayout);
  }, [modules, setLayout]);

  const onLayoutChange = useCallback(
    (newLayout: GridLayoutItem[]) => {
      setLayout(newLayout);
      // Debounced save to backend
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        newLayout.forEach((item) => {
          const module = modules.find((m) => m.id === item.i);
          if (module) {
            updateModuleLayout(item.i, {
              position_x: item.x,
              position_y: item.y,
              width: item.w,
              height: item.h,
            }).catch(console.error);
          }
        });
      }, 500);
    },
    [modules, setLayout]
  );

  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={{ lg: layout, md: layout, sm: layout, xs: layout }}
      breakpoints={GRID_CONFIG.breakpoints}
      cols={GRID_CONFIG.cols}
      rowHeight={GRID_CONFIG.rowHeight}
      margin={GRID_CONFIG.margin}
      isDraggable={isEditMode}
      isResizable={isEditMode}
      onLayoutChange={onLayoutChange}
      draggableHandle=".drag-handle"
    >
      {modules.map((module) => (
        <div key={module.id} className="glass-card rounded-xl overflow-hidden">
          {isEditMode && (
            <div className="drag-handle h-6 bg-dark-700/50 flex items-center justify-center cursor-move border-b border-dark-600">
              <div className="w-8 h-1 rounded-full bg-dark-500" />
            </div>
          )}
          <div className={cn("p-4", isEditMode && "pt-2")}>
            <ModuleCard module={module} />
          </div>
        </div>
      ))}
    </ResponsiveGridLayout>
  );
}
