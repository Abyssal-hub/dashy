import { useState, useRef, useEffect } from "react";
import { X, Check, Expand } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { format } from "date-fns";

interface QuickAddProps {
  date: Date;
  onClose: () => void;
  onExpand: (date: Date) => void;
  onSave: (event: { title: string; start_time: string; end_time: string }) => void;
}

export function QuickAdd({ date, onClose, onExpand, onSave }: QuickAddProps) {
  const [title, setTitle] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      if (e.key === "Enter" && title.trim()) {
        const start = new Date(date);
        const end = new Date(date);
        end.setHours(end.getHours() + 1);
        onSave({
          title: title.trim(),
          start_time: start.toISOString(),
          end_time: end.toISOString(),
        });
        onClose();
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [date, title, onClose, onSave]);

  return (
    <div className="glass-card rounded-lg p-3 w-[280px] shadow-2xl border border-dark-500 z-[100]"
      style={{ animation: "popoverIn 150ms ease-out" }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Input
          ref={inputRef}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Event title..."
          className="h-8 text-sm"
        />
      </div>
      <div className="text-xs text-gray-500 mb-2">
        {format(date, "MMM d, yyyy h:mm a")} (1 hr)
      </div>
      <div className="flex gap-1.5">
        <Button
          size="sm"
          className="h-7 text-xs gap-1"
          disabled={!title.trim()}
          onClick={() => {
            const start = new Date(date);
            const end = new Date(date);
            end.setHours(end.getHours() + 1);
            onSave({
              title: title.trim(),
              start_time: start.toISOString(),
              end_time: end.toISOString(),
            });
            onClose();
          }}
        >
          <Check className="w-3 h-3" />
          Save
        </Button>
        <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" onClick={onClose}>
          <X className="w-3 h-3" />
          Cancel
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 text-xs gap-1 ml-auto"
          onClick={() => onExpand(date)}
        >
          <Expand className="w-3 h-3" />
          Full
        </Button>
      </div>
    </div>
  );
}
