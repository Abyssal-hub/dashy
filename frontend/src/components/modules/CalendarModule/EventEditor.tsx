import { useState, useEffect } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { CalendarEvent } from "./hooks/useCalendar";
import { getEventColor } from "./hooks/useCalendar";
import { format, parseISO } from "date-fns";

interface EventEditorProps {
  event?: CalendarEvent | null;
  initialDate?: Date | null;
  open: boolean;
  onClose: () => void;
  onSave: (event: Partial<CalendarEvent>) => void;
}

const EVENT_TYPES = ["earnings", "dividend", "economic", "meeting"];

export function EventEditor({ event, initialDate, open, onClose, onSave }: EventEditorProps) {
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [type, setType] = useState("meeting");
  const [sourceUrl, setSourceUrl] = useState("");
  const [allDay, setAllDay] = useState(false);

  useEffect(() => {
    if (event) {
      setTitle(event.title);
      const s = parseISO(event.start_time);
      const e = parseISO(event.end_time);
      setDate(format(s, "yyyy-MM-dd"));
      setStartTime(format(s, "HH:mm"));
      setEndTime(format(e, "HH:mm"));
      setType(event.calendar_type);
      setSourceUrl(event.source_url || "");
      setAllDay(event.all_day);
    } else if (initialDate) {
      setTitle("");
      setDate(format(initialDate, "yyyy-MM-dd"));
      setStartTime(format(initialDate, "HH:mm"));
      const end = new Date(initialDate);
      end.setHours(end.getHours() + 1);
      setEndTime(format(end, "HH:mm"));
      setType("meeting");
      setSourceUrl("");
      setAllDay(false);
    }
  }, [event, initialDate, open]);

  function handleSave() {
    if (!title.trim()) return;
    const start = new Date(`${date}T${startTime}`);
    const end = new Date(`${date}T${endTime}`);
    onSave({
      id: event?.id,
      title: title.trim(),
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      all_day: allDay,
      calendar_type: type,
      source_url: sourceUrl || undefined,
    });
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-[560px]">
        <DialogHeader>
          <DialogTitle>{event ? "Edit Event" : "New Event"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Title</label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Event title"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Date</label>
              <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Type</label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-dark-500 bg-dark-800 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-accent-purple/50"
              >
                {EVENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Start Time</label>
              <Input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                disabled={allDay}
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">End Time</label>
              <Input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                disabled={allDay}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="allDay"
              checked={allDay}
              onChange={(e) => setAllDay(e.target.checked)}
              className="rounded border-dark-500 bg-dark-800"
            />
            <label htmlFor="allDay" className="text-sm text-gray-300">
              All day
            </label>
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1">Source URL</label>
            <Input
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://..."
            />
          </div>

          <div className="flex items-center gap-2 mt-2">
            {EVENT_TYPES.map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
                  type === t ? "bg-dark-600" : ""
                }`}
              >
                <div
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: getEventColor(t) }}
                />
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6 pt-4 border-t border-dark-600">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!title.trim()} className="gap-2">
            <Save className="w-4 h-4" />
            Save
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
