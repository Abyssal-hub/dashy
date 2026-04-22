import { useCallback } from "react";
import { Calendar as CalendarIcon, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useCalendar } from "./hooks/useCalendar";
import { MonthView } from "./MonthView";
import { WeekView } from "./WeekView";
import { EventEditor } from "./EventEditor";
import type { Module } from "@/types";

interface CalendarModuleProps {
  module: Module;
  data?: Record<string, unknown>;
  isLoading: boolean;
}

export default function CalendarModule({ module, isLoading }: CalendarModuleProps) {
  const {
    state,
    events,
    isLoading: calendarLoading,
    setView,
    setCurrentDate,
    openEditor,
    closeEditor,
    goToToday,
  } = useCalendar(module.id);

  const handleGoToWeek = useCallback(
    (date: Date) => {
      setCurrentDate(date);
      setView("week");
    },
    [setCurrentDate, setView]
  );

  const handleSaveEvent = useCallback(
    (evt: Partial<import("./hooks/useCalendar").CalendarEvent>) => {
      // In a real implementation, this would POST to the API
      console.log("Save event:", evt);
      closeEditor();
    },
    [closeEditor]
  );

  if (isLoading || calendarLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 text-accent-purple animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-2 px-1 shrink-0">
        <div className="flex items-center gap-1 bg-dark-800 rounded-lg p-0.5">
          <button
            onClick={() => setView("month")}
            className={cn(
              "px-3 py-1 text-xs font-medium rounded-md transition-all",
              state.view === "month"
                ? "bg-dark-600 text-white"
                : "text-gray-400 hover:text-white"
            )}
          >
            Month
          </button>
          <button
            onClick={() => setView("week")}
            className={cn(
              "px-3 py-1 text-xs font-medium rounded-md transition-all",
              state.view === "week"
                ? "bg-dark-600 text-white"
                : "text-gray-400 hover:text-white"
            )}
          >
            Week
          </button>
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1.5 text-gray-400 hover:text-white"
            onClick={goToToday}
          >
            <CalendarIcon className="w-3.5 h-3.5" />
            Today
          </Button>
        </div>
      </div>

      {/* View content with fade transition */}
      <div className="flex-1 min-h-0 relative">
        <div
          className={cn(
            "h-full transition-opacity duration-200",
            state.view === "month" ? "opacity-100" : "opacity-0 pointer-events-none absolute inset-0"
          )}
        >
          <MonthView
            currentDate={state.currentDate}
            events={events}
            onDateChange={setCurrentDate}
            onOpenEditor={openEditor}
            onGoToWeek={handleGoToWeek}
          />
        </div>

        <div
          className={cn(
            "h-full transition-opacity duration-200",
            state.view === "week" ? "opacity-100" : "opacity-0 pointer-events-none absolute inset-0"
          )}
        >
          <WeekView
            currentDate={state.currentDate}
            events={events}
            onDateChange={setCurrentDate}
            onOpenEditor={openEditor}
          />
        </div>
      </div>

      {/* Full editor modal */}
      <EventEditor
        event={state.selectedEvent}
        initialDate={state.quickAddDate}
        open={state.isEditorOpen}
        onClose={closeEditor}
        onSave={handleSaveEvent}
      />
    </div>
  );
}
