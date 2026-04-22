import { useQuery } from "@tanstack/react-query";
import { getModuleData } from "@/lib/api";
import { useState, useCallback } from "react";

export interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  calendar_type: "earnings" | "dividend" | "economic" | "meeting" | string;
  source_url?: string;
  metadata?: {
    description?: string;
    location?: string;
    [key: string]: unknown;
  };
}

export type CalendarView = "month" | "week";

export interface CalendarState {
  view: CalendarView;
  currentDate: Date;
  selectedEvent: CalendarEvent | null;
  isPopoverOpen: boolean;
  isEditorOpen: boolean;
  quickAddDate: Date | null;
}

export const EVENT_TYPE_COLORS: Record<string, string> = {
  earnings: "#34a853",
  dividend: "#fbbc04",
  economic: "#ea4335",
  meeting: "#9334e6",
  default: "#4285f4",
};

export function getEventColor(type: string): string {
  return EVENT_TYPE_COLORS[type] || EVENT_TYPE_COLORS.default;
}

export function useCalendar(moduleId: string) {
  const [state, setState] = useState<CalendarState>({
    view: "week",
    currentDate: new Date(),
    selectedEvent: null,
    isPopoverOpen: false,
    isEditorOpen: false,
    quickAddDate: null,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["calendarData", moduleId],
    queryFn: () => getModuleData(moduleId),
    enabled: !!moduleId,
  });

  const events: CalendarEvent[] = (data?.data?.events as CalendarEvent[]) || [];

  const setView = useCallback((view: CalendarView) => {
    setState((s) => ({ ...s, view }));
  }, []);

  const setCurrentDate = useCallback((date: Date) => {
    setState((s) => ({ ...s, currentDate: date }));
  }, []);

  const selectEvent = useCallback((event: CalendarEvent | null) => {
    setState((s) => ({
      ...s,
      selectedEvent: event,
      isPopoverOpen: event !== null,
      isEditorOpen: false,
      quickAddDate: null,
    }));
  }, []);

  const openEditor = useCallback((event?: CalendarEvent) => {
    setState((s) => ({
      ...s,
      selectedEvent: event || null,
      isEditorOpen: true,
      isPopoverOpen: false,
      quickAddDate: null,
    }));
  }, []);

  const closePopover = useCallback(() => {
    setState((s) => ({ ...s, isPopoverOpen: false, selectedEvent: null }));
  }, []);

  const closeEditor = useCallback(() => {
    setState((s) => ({ ...s, isEditorOpen: false, selectedEvent: null }));
  }, []);

  const openQuickAdd = useCallback((date: Date) => {
    setState((s) => ({
      ...s,
      quickAddDate: date,
      isPopoverOpen: false,
      selectedEvent: null,
    }));
  }, []);

  const closeQuickAdd = useCallback(() => {
    setState((s) => ({ ...s, quickAddDate: null }));
  }, []);

  const goToToday = useCallback(() => {
    setState((s) => ({ ...s, currentDate: new Date() }));
  }, []);

  return {
    state,
    events,
    isLoading,
    refetch,
    setView,
    setCurrentDate,
    selectEvent,
    openEditor,
    closePopover,
    closeEditor,
    openQuickAdd,
    closeQuickAdd,
    goToToday,
  };
}
