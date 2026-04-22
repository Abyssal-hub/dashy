import { useRef, useEffect } from "react";
import { X, ExternalLink, Pencil, Trash2, Clock, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getEventColor } from "./hooks/useCalendar";
import type { CalendarEvent } from "./hooks/useCalendar";
import { format, parseISO } from "date-fns";

interface EventPopoverProps {
  event: CalendarEvent;
  anchorEl: HTMLElement | null;
  onClose: () => void;
  onEdit: (event: CalendarEvent) => void;
}

export function EventPopover({ event, anchorEl, onClose, onEdit }: EventPopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);
  const color = getEventColor(event.calendar_type);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [onClose]);

  // Position relative to anchor
  const [top, left] = (() => {
    if (!anchorEl) return [100, 100];
    const rect = anchorEl.getBoundingClientRect();
    return [rect.bottom + 8, rect.left];
  })();

  const start = parseISO(event.start_time);
  const end = parseISO(event.end_time);
  const timeStr = event.all_day
    ? "All day"
    : `${format(start, "h:mm a")} – ${format(end, "h:mm a")}`;

  return (
    <div
      ref={popoverRef}
      className="fixed z-[100] glass-card rounded-lg p-4 w-[320px] shadow-2xl border border-dark-500"
      style={{
        top,
        left: Math.min(left, window.innerWidth - 340),
        animation: "popoverIn 150ms ease-out",
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: color }}
          />
          <h3 className="font-semibold text-white text-base leading-tight">
            {event.title}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-gray-300">
          <Clock className="w-4 h-4 text-gray-500" />
          <span>{timeStr}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="px-2 py-0.5 rounded text-xs font-medium text-white"
            style={{ backgroundColor: color }}
          >
            {event.calendar_type}
          </span>
        </div>
        {event.source_url && (
          <div className="flex items-center gap-2 text-gray-300">
            <Link2 className="w-4 h-4 text-gray-500" />
            <a
              href={event.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent-purple hover:underline flex items-center gap-1"
            >
              View Source
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        )}
        {event.metadata?.description && (
          <p className="text-gray-400 text-xs mt-2">{event.metadata.description}</p>
        )}
      </div>

      <div className="flex gap-2 mt-4 pt-3 border-t border-dark-600">
        <Button
          size="sm"
          variant="outline"
          className="gap-1.5 flex-1"
          onClick={() => onEdit(event)}
        >
          <Pencil className="w-3.5 h-3.5" />
          Edit
        </Button>
        <Button
          size="sm"
          variant="destructive"
          className="gap-1.5 flex-1"
          onClick={() => {
            // Delete handler would go here
            onClose();
          }}
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete
        </Button>
      </div>
    </div>
  );
}
