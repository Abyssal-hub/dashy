import { useState, useEffect, useCallback, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { getLogStreamUrl, getLogs } from "@/lib/api";
import type { LogEntry } from "@/types";

export function useLogStream(severity?: string, source?: string) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const seenRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const url = getLogStreamUrl({ severity, source });
    const eventSource = new EventSource(url);

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const entry = JSON.parse(event.data) as LogEntry;
        const id = entry.id;
        if (id && seenRef.current.has(id)) {
          return;
        }
        if (id) {
          seenRef.current.add(id);
          // Prevent unbounded growth
          if (seenRef.current.size > 1000) {
            const items = Array.from(seenRef.current);
            seenRef.current = new Set(items.slice(-500));
          }
        }
        setLogs((prev) => {
          const newLogs = [entry, ...prev];
          return newLogs.slice(0, 500);
        });
      } catch {
        // Ignore malformed JSON
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
      setIsConnected(false);
    };
  }, [severity, source]);

  const clearLogs = useCallback(() => {
    setLogs([]);
    seenRef.current.clear();
  }, []);

  return { logs, isConnected, clearLogs };
}

export function useLogs(
  params?: {
    severity?: string;
    source?: string;
    limit?: number;
    offset?: number;
  }
) {
  return useQuery<{ logs: LogEntry[]; total: number; limit: number; offset: number }>({
    queryKey: ["logs", params],
    queryFn: () => getLogs(params),
  });
}
