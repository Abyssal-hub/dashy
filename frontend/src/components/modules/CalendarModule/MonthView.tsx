import { useMemo, useState, useCallback } from "react";
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isToday,
  format,
  parseISO,
} from "date-fns";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getEventColor } from "./hooks/useCalendar";
import type { CalendarEvent } from "./hooks/useCalendar";
import { EventPopover } from "./EventPopover";
import { QuickAdd } from "./QuickAdd";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MAX_CHIPS = 3;

interface MonthViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  onDateChange: (date: Date) => void;
  onOpenEditor: (event?: CalendarEvent) => void;
  onGoToWeek: (date: Date) => void;
}

export function MonthView({
  currentDate,
  events,
  onDateChange,
  onOpenEditor,
  onGoToWeek,
}: MonthViewProps) {
  const [popoverEvent, setPopoverEvent] = useState<CalendarEvent | null>(null);
  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null);
  const [quickAddDate, setQuickAddDate] = useState<Date | null>(null);
  const [quickAddAnchor, setQuickAddAnchor] = useState<HTMLElement | null>(null);

  const days = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 });
    const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [currentDate]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    events.forEach((event) => {
      const date = parseISO(event.start_time);
      const key = format(date, "yyyy-MM-dd");
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(event);
    });
    return map;
  }, [events]);

  const handlePrevMonth = useCallback(() => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() - 1);
    onDateChange(d);
  }, [currentDate, onDateChange]);

  const handleNextMonth = useCallback(() => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() + 1);
    onDateChange(d);
  }, [currentDate, onDateChange]);

  const handleEventClick = useCallback((e: React.MouseEvent, event: CalendarEvent) => {
    e.stopPropagation();
    setPopoverEvent(event);
    setPopoverAnchor(e.currentTarget as HTMLElement);
  }, []);

  const handleDayClick = useCallback((e: React.MouseEvent, day: Date) => {
    // If clicked on empty space (not on a chip), open quick add
    if ((e.target as HTMLElement).closest("[data-event-chip]")) return;
    setQuickAddDate(day);
    setQuickAddAnchor(e.currentTarget as HTMLElement);
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handlePrevMonth}>
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <h3 className="font-semibold text-white text-sm min-w-[110px] text-center">
            {format(currentDate, "MMMM yyyy")}
          </h3>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNextMonth}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-px mb-1">
        {WEEKDAYS.map((day) => (
          <div key={day} className="text-center text-xs text-gray-500 font-medium py-1">
            {day}
          </div>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-px flex-1 min-h-0">
        {days.map((day) => {
          const dayKey = format(day, "yyyy-MM-dd");
          const dayEvents = eventsByDay.get(dayKey) || [];
          const visibleEvents = dayEvents.slice(0, MAX_CHIPS);
          const overflow = dayEvents.length - MAX_CHIPS;
          const isCurrentMonth = isSameMonth(day, currentDate);
          const dayIsToday = isToday(day);

          return (
            <div
              key={dayKey}
              className={`
                relative min-h-[80px] p-1 border border-dark-700/50 cursor-pointer
                hover:bg-dark-700/30 transition-colors
                ${!isCurrentMonth ? "opacity-40" : ""}
              `}
              onClick={(e) => handleDayClick(e, day)}
            >
              {/* Day number */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onGoToWeek(day);
                }}
                className={`
                  text-xs font-medium mb-1 block
                  ${dayIsToday
                    ? "w-6 h-6 rounded-full bg-accent-blue text-white flex items-center justify-center"
                    : isCurrentMonth
                    ? "text-gray-300"
                    : "text-gray-600"
                  }
                `}
              >
                {format(day, "d")}
              </button>

              {/* Event chips */}
              <div className="space-y-0.5">
                {visibleEvents.map((event) => (
                  <div
                    key={event.id}
                    data-event-chip
                    onClick={(e) => handleEventClick(e, event)}
                    className="h-5 rounded px-2 flex items-center cursor-pointer hover:brightness-110 transition-all hover:translate-y-[-1px]"
                    style={{
                      backgroundColor: getEventColor(event.calendar_type),
                    }}
                    title={event.title}
                  >
                    <span className="text-[11px] text-white font-medium truncate">
                      {event.title}
                    </span>
                  </div>
                ))}
                {overflow > 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Show expanded view with all events
                      if (dayEvents[0]) {
                        setPopoverEvent(dayEvents[0]);
                        setPopoverAnchor(e.currentTarget as HTMLElement);
                      }
                    }}
                    className="text-[11px] text-accent-blue hover:underline px-1"
                  >
                    +{overflow} more
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Popover */}
      {popoverEvent && popoverAnchor && (
        <EventPopover
          event={popoverEvent}
          anchorEl={popoverAnchor}
          onClose={() => {
            setPopoverEvent(null);
            setPopoverAnchor(null);
          }}
          onEdit={(evt) => {
            setPopoverEvent(null);
            setPopoverAnchor(null);
            onOpenEditor(evt);
          }}
        />
      )}

      {/* Quick Add */}
      {quickAddDate && quickAddAnchor && (
        <div
          className="fixed z-[100]"
          style={{
            top: (quickAddAnchor.getBoundingClientRect().bottom + 4),
            left: quickAddAnchor.getBoundingClientRect().left,
          }}
        >
          <QuickAdd
            date={quickAddDate}
            onClose={() => {
              setQuickAddDate(null);
              setQuickAddAnchor(null);
            }}
            onExpand={(_date) => {
              setQuickAddDate(null);
              setQuickAddAnchor(null);
              onOpenEditor();
            }}
            onSave={() => {
              setQuickAddDate(null);
              setQuickAddAnchor(null);
            }}
          />
        </div>
      )}
    </div>
  );
}
