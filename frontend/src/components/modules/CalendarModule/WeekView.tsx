import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import {
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  format,
  parseISO,
  isSameDay,
  isToday,
} from "date-fns";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getEventColor } from "./hooks/useCalendar";
import type { CalendarEvent } from "./hooks/useCalendar";
import { EventPopover } from "./EventPopover";
import { QuickAdd } from "./QuickAdd";

const SLOT_HEIGHT = 48; // px per 30-min slot
const SLOTS_PER_HOUR = 2;
const HOURS = 24;
const TOTAL_SLOTS = HOURS * SLOTS_PER_HOUR;
const GRID_HEIGHT = TOTAL_SLOTS * SLOT_HEIGHT;
const TIME_COLUMN_WIDTH = 50;

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface WeekViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  onDateChange: (date: Date) => void;
  onOpenEditor: (event?: CalendarEvent) => void;
}

interface PositionedEvent {
  event: CalendarEvent;
  top: number;
  height: number;
  left: number;
  width: number;
  dayIndex: number;
}

function getMinutesFromMidnight(date: Date): number {
  return date.getHours() * 60 + date.getMinutes();
}

function computeOverlapLayout(dayEvents: CalendarEvent[], dayIndex: number): PositionedEvent[] {
  // Sort by start time
  const sorted = [...dayEvents].sort((a, b) => {
    return parseISO(a.start_time).getTime() - parseISO(b.start_time).getTime();
  });

  const positioned: PositionedEvent[] = [];
  const clusters: { events: CalendarEvent[]; maxCols: number }[] = [];

  // Group into overlap clusters
  let currentCluster: CalendarEvent[] = [];
  let clusterEnd = -1;

  for (const event of sorted) {
    const start = getMinutesFromMidnight(parseISO(event.start_time));
    const end = getMinutesFromMidnight(parseISO(event.end_time));

    if (currentCluster.length === 0 || start < clusterEnd) {
      currentCluster.push(event);
      clusterEnd = Math.max(clusterEnd, end);
    } else {
      clusters.push({ events: currentCluster, maxCols: 0 });
      currentCluster = [event];
      clusterEnd = end;
    }
  }
  if (currentCluster.length > 0) {
    clusters.push({ events: currentCluster, maxCols: 0 });
  }

  // Within each cluster, assign columns
  for (const cluster of clusters) {
    const cols: { end: number; events: CalendarEvent[] }[] = [];
    for (const event of cluster.events) {
      const start = getMinutesFromMidnight(parseISO(event.start_time));
      const end = getMinutesFromMidnight(parseISO(event.end_time));

      let placed = false;
      for (const col of cols) {
        if (start >= col.end) {
          col.end = end;
          col.events.push(event);
          placed = true;
          break;
        }
      }
      if (!placed) {
        cols.push({ end, events: [event] });
      }
    }
    cluster.maxCols = cols.length;

    // Create positioned events
    const colMap = new Map<string, number>();
    cols.forEach((col, colIdx) => {
      col.events.forEach((evt) => colMap.set(evt.id, colIdx));
    });

    for (const event of cluster.events) {
      const start = parseISO(event.start_time);
      const end = parseISO(event.end_time);
      const startMin = getMinutesFromMidnight(start);
      const endMin = getMinutesFromMidnight(end);
      const duration = Math.max(endMin - startMin, 30); // min 30 min
      const colIdx = colMap.get(event.id) || 0;
      const width = 100 / cluster.maxCols;
      const left = colIdx * width;

      positioned.push({
        event,
        top: (startMin / 1440) * GRID_HEIGHT,
        height: (duration / 1440) * GRID_HEIGHT,
        left,
        width,
        dayIndex,
      });
    }
  }

  return positioned;
}

export function WeekView({
  currentDate,
  events,
  onDateChange,
  onOpenEditor,
}: WeekViewProps) {
  const [popoverEvent, setPopoverEvent] = useState<CalendarEvent | null>(null);
  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null);
  const [quickAddDate, setQuickAddDate] = useState<Date | null>(null);
  const [quickAddAnchor, setQuickAddAnchor] = useState<HTMLElement | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const scrollRef = useRef<HTMLDivElement>(null);

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(interval);
  }, []);

  // Scroll to 8 AM on mount/date change
  useEffect(() => {
    if (scrollRef.current) {
      const eightAmSlot = 8 * SLOTS_PER_HOUR * SLOT_HEIGHT;
      scrollRef.current.scrollTop = eightAmSlot - 50;
    }
  }, [currentDate]);

  const days = useMemo(() => {
    const weekStart = startOfWeek(currentDate, { weekStartsOn: 1 });
    const weekEnd = endOfWeek(currentDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start: weekStart, end: weekEnd });
  }, [currentDate]);

  // Separate all-day and timed events
  const { allDayEvents, timedEvents } = useMemo(() => {
    const allDay: CalendarEvent[] = [];
    const timed: CalendarEvent[] = [];
    events.forEach((e) => {
      if (e.all_day) allDay.push(e);
      else timed.push(e);
    });
    return { allDayEvents: allDay, timedEvents: timed };
  }, [events]);

  // Group timed events by day and compute positions
  const positionedEvents = useMemo(() => {
    const result: PositionedEvent[] = [];
    days.forEach((day, dayIndex) => {
      const dayEvents = timedEvents.filter((e) =>
        isSameDay(parseISO(e.start_time), day)
      );
      const positioned = computeOverlapLayout(dayEvents, dayIndex);
      result.push(...positioned);
    });
    return result;
  }, [timedEvents, days]);

  const handlePrevWeek = useCallback(() => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - 7);
    onDateChange(d);
  }, [currentDate, onDateChange]);

  const handleNextWeek = useCallback(() => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + 7);
    onDateChange(d);
  }, [currentDate, onDateChange]);

  const handleEventClick = useCallback((e: React.MouseEvent, event: CalendarEvent) => {
    e.stopPropagation();
    setPopoverEvent(event);
    setPopoverAnchor(e.currentTarget as HTMLElement);
  }, []);

  const handleSlotClick = useCallback((e: React.MouseEvent, day: Date, slotIndex: number) => {
    if ((e.target as HTMLElement).closest("[data-event-block]")) return;
    const hour = Math.floor(slotIndex / SLOTS_PER_HOUR);
    const minute = (slotIndex % SLOTS_PER_HOUR) * 30;
    const date = new Date(day);
    date.setHours(hour, minute, 0, 0);
    setQuickAddDate(date);
    setQuickAddAnchor(e.currentTarget as HTMLElement);
  }, []);

  const currentTimeTop = useMemo(() => {
    const now = currentTime;
    const mins = now.getHours() * 60 + now.getMinutes();
    return (mins / 1440) * GRID_HEIGHT;
  }, [currentTime]);

  const isCurrentWeek = days.some((d) => isToday(d));

  // Time slots
  const timeSlots = useMemo(() => {
    return Array.from({ length: TOTAL_SLOTS }, (_, i) => {
      const hour = Math.floor(i / SLOTS_PER_HOUR);
      const minute = (i % SLOTS_PER_HOUR) * 30;
      return { hour, minute, label: minute === 0 ? format(new Date().setHours(hour, 0), "h a") : "" };
    });
  }, []);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 px-1 shrink-0">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handlePrevWeek}>
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <h3 className="font-semibold text-white text-sm">
            {format(days[0], "MMM d")} – {format(days[6], "MMM d, yyyy")}
          </h3>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNextWeek}>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Day headers + all-day row */}
      <div className="shrink-0">
        <div className="flex" style={{ marginLeft: TIME_COLUMN_WIDTH }}>
          {days.map((day, i) => (
            <div
              key={i}
              className={`
                flex-1 text-center py-2 border-b border-dark-600
                ${isToday(day) ? "bg-accent-purple/10" : ""}
              `}
            >
              <div className="text-[10px] text-gray-500 uppercase">{WEEKDAYS[i]}</div>
              <div
                className={`
                  text-sm font-semibold mt-0.5
                  ${isToday(day) ? "text-accent-purple" : "text-white"}
                `}
              >
                {format(day, "d")}
              </div>
            </div>
          ))}
        </div>

        {/* All-day events row */}
        <div className="flex" style={{ marginLeft: TIME_COLUMN_WIDTH }}>
          {days.map((day, i) => {
            const dayAllDay = allDayEvents.filter((e) =>
              isSameDay(parseISO(e.start_time), day)
            );
            return (
              <div
                key={i}
                className="flex-1 min-h-[28px] border-b border-dark-600 p-0.5 space-y-0.5"
              >
                {dayAllDay.map((event) => (
                  <div
                    key={event.id}
                    data-event-block
                    onClick={(e) => handleEventClick(e, event)}
                    className="h-6 rounded px-2 flex items-center cursor-pointer hover:brightness-110 transition-all"
                    style={{ backgroundColor: getEventColor(event.calendar_type) }}
                  >
                    <span className="text-[11px] text-white font-medium truncate">
                      {event.title}
                    </span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {/* Time grid */}
      <div ref={scrollRef} className="flex-1 overflow-auto relative">
        <div className="flex" style={{ height: GRID_HEIGHT }}>
          {/* Time column */}
          <div
            className="shrink-0 border-r border-dark-600 relative"
            style={{ width: TIME_COLUMN_WIDTH }}
          >
            {timeSlots.map((slot, i) => (
              <div
                key={i}
                className="absolute right-1 text-[10px] text-gray-500 text-right"
                style={{ top: i * SLOT_HEIGHT - 6 }}
              >
                {slot.label}
              </div>
            ))}
            {/* Current time dot on time column */}
            {isCurrentWeek && (
              <div
                className="absolute right-0 w-2 h-2 rounded-full bg-[#ea4335] z-20"
                style={{ top: currentTimeTop - 4 }}
              />
            )}
          </div>

          {/* Day columns */}
          {days.map((day, dayIndex) => (
            <div
              key={dayIndex}
              className={`
                flex-1 relative border-r border-dark-600/50
                ${isToday(day) ? "bg-accent-purple/5" : ""}
              `}
            >
              {/* Hour lines */}
              {Array.from({ length: HOURS }, (_, h) => (
                <div
                  key={h}
                  className="absolute w-full border-t border-dark-700/30"
                  style={{ top: h * SLOTS_PER_HOUR * SLOT_HEIGHT }}
                />
              ))}

              {/* Half-hour lines */}
              {Array.from({ length: HOURS }, (_, h) => (
                <div
                  key={`half-${h}`}
                  className="absolute w-full border-t border-dark-700/10"
                  style={{ top: (h * SLOTS_PER_HOUR + 1) * SLOT_HEIGHT }}
                />
              ))}

              {/* Clickable slots */}
              {timeSlots.map((_, slotIndex) => (
                <div
                  key={slotIndex}
                  className="absolute w-full hover:bg-dark-700/20 transition-colors"
                  style={{
                    top: slotIndex * SLOT_HEIGHT,
                    height: SLOT_HEIGHT,
                  }}
                  onClick={(e) => handleSlotClick(e, day, slotIndex)}
                />
              ))}

              {/* Positioned events */}
              {positionedEvents
                .filter((pe) => pe.dayIndex === dayIndex)
                .map((pe) => (
                  <div
                    key={pe.event.id}
                    data-event-block
                    onClick={(e) => handleEventClick(e, pe.event)}
                    className="absolute rounded px-2 py-1 cursor-pointer hover:brightness-110 transition-all hover:shadow-lg border border-white/10 overflow-hidden"
                    style={{
                      top: pe.top,
                      height: Math.max(pe.height, 24),
                      left: `${pe.left}%`,
                      width: `${pe.width}%`,
                      backgroundColor: getEventColor(pe.event.calendar_type),
                    }}
                  >
                    <div className="text-white font-medium text-[12px] leading-tight truncate">
                      {pe.event.title}
                    </div>
                    {pe.height >= 36 && (
                      <div className="text-white/80 text-[10px] leading-tight mt-0.5">
                        {format(parseISO(pe.event.start_time), "h:mm a")} –{" "}
                        {format(parseISO(pe.event.end_time), "h:mm a")}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          ))}

          {/* Current time line */}
          {isCurrentWeek && (
            <div
              className="absolute left-0 right-0 pointer-events-none z-10"
              style={{ top: currentTimeTop }}
            >
              <div className="flex">
                <div className="shrink-0" style={{ width: TIME_COLUMN_WIDTH }} />
                <div className="flex-1 relative">
                  <div className="absolute left-0 right-0 h-[2px] bg-[#ea4335]" />
                </div>
              </div>
            </div>
          )}
        </div>
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
            top: quickAddAnchor.getBoundingClientRect().bottom + 4,
            left: Math.min(
              quickAddAnchor.getBoundingClientRect().left,
              window.innerWidth - 300
            ),
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
