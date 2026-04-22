import { useState, useCallback, useRef, useEffect } from "react";
import {
  Search,
  Download,
  Trash2,
  Wifi,
  WifiOff,
  Filter,
  X,
  AlertCircle,
  Info,
  AlertTriangle,
} from "lucide-react";
import { useLogStream, useLogs } from "@/hooks/useLogs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, downloadJSON, downloadCSV, formatDate, getSeverityColor, getSeverityBgColor } from "@/lib/utils";
import type { LogEntry } from "@/types";

const SEVERITY_OPTIONS = [
  { value: "", label: "All Severities" },
  { value: "INFO", label: "Info" },
  { value: "WARN", label: "Warning" },
  { value: "ERROR", label: "Error" },
];

export function LogViewer() {
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isStreamMode, setIsStreamMode] = useState(true);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // SSE streaming
  const { logs: streamLogs, isConnected, clearLogs } = useLogStream(
    severityFilter || undefined,
    sourceFilter || undefined
  );

  // Polling fallback
  const { data: polledLogs } = useLogs(
    isStreamMode
      ? undefined
      : {
          severity: severityFilter || undefined,
          source: sourceFilter || undefined,
          limit: 50,
          offset: 0,
        }
  );

  const logs: LogEntry[] = isStreamMode ? streamLogs : (polledLogs?.logs ?? []);

  // Auto-scroll to bottom for streaming
  useEffect(() => {
    if (isStreamMode && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamLogs.length, isStreamMode]);

  const filteredLogs = logs.filter((log) => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        log.message.toLowerCase().includes(q) ||
        log.source.toLowerCase().includes(q) ||
        log.severity.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleExportJSON = useCallback(() => {
    downloadJSON(filteredLogs, `logs-${new Date().toISOString()}.json`);
  }, [filteredLogs]);

  const handleExportCSV = useCallback(() => {
    const headers = ["timestamp", "severity", "source", "message"];
    const rows = filteredLogs.map((log) => [
      log.timestamp,
      log.severity,
      log.source,
      log.message,
    ]);
    downloadCSV(headers, rows, `logs-${new Date().toISOString()}.csv`);
  }, [filteredLogs]);

  const clearAllLogs = useCallback(() => {
    clearLogs();
  }, [clearLogs]);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "ERROR":
        return <AlertCircle className="w-4 h-4 text-status-critical" />;
      case "WARN":
        return <AlertTriangle className="w-4 h-4 text-status-warning" />;
      case "INFO":
        return <Info className="w-4 h-4 text-status-info" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-dark-700 bg-dark-850/50">
        {/* Connection status */}
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Wifi className="w-4 h-4 text-status-online" />
          ) : (
            <WifiOff className="w-4 h-4 text-status-warning" />
          )}
          <span className={cn("text-xs font-medium", isConnected ? "text-status-online" : "text-status-warning")}>
            {isConnected ? "LIVE" : "RECONNECTING"}
          </span>
        </div>

        {/* Stream toggle */}
        <div className="flex items-center bg-dark-700 rounded-lg p-0.5">
          <button
            onClick={() => setIsStreamMode(true)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium rounded-md transition-all",
              isStreamMode ? "bg-accent-violet text-white" : "text-gray-400 hover:text-white"
            )}
          >
            Stream
          </button>
          <button
            onClick={() => setIsStreamMode(false)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium rounded-md transition-all",
              !isStreamMode ? "bg-accent-violet text-white" : "text-gray-400 hover:text-white"
            )}
          >
            Static
          </button>
        </div>

        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-8 text-sm"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              <X className="w-3.5 h-3.5 text-gray-500 hover:text-white" />
            </button>
          )}
        </div>

        {/* Severity filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
          <Select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="pl-9 h-8 text-sm w-36"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </Select>
        </div>

        {/* Source filter */}
        <Input
          placeholder="Source filter"
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="h-8 text-sm w-32"
        />

        {/* Actions */}
        <div className="flex items-center gap-1 ml-auto">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleExportJSON}
            title="Export JSON"
            className="h-8 w-8"
          >
            <Download className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleExportCSV}
            title="Export CSV"
            className="h-8 w-8"
          >
            <span className="text-xs font-bold">CSV</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={clearAllLogs}
            title="Clear logs"
            className="h-8 w-8 text-status-critical hover:text-red-400"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-dark-700 bg-dark-800/30">
        <span className="text-xs text-gray-500">
          Showing <strong className="text-gray-300">{filteredLogs.length}</strong> entries
        </span>
        <div className="flex items-center gap-2">
          {["INFO", "WARN", "ERROR"].map((sev: string) => {
            const count = filteredLogs.filter((l: LogEntry) => l.severity === sev).length;
            return (
              <Badge
                key={sev}
                variant={sev.toLowerCase() as "info" | "warning" | "destructive"}
                className="text-xs"
              >
                {sev}: {count}
              </Badge>
            );
          })}
        </div>
      </div>

      {/* Log entries */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="space-y-0.5 p-2">
          {filteredLogs.map((log: LogEntry) => (
            <button
              key={log.id}
              onClick={() => setSelectedLog(log)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-lg text-sm transition-all flex items-start gap-2",
                getSeverityBgColor(log.severity),
                selectedLog?.id === log.id && "ring-1 ring-accent-purple/50"
              )}
            >
              {getSeverityIcon(log.severity)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 text-xs">{formatDate(log.timestamp)}</span>
                  <span className={cn("text-xs font-medium", getSeverityColor(log.severity))}>
                    {log.severity}
                  </span>
                  <Badge variant="secondary" className="text-xs">
                    {log.source}
                  </Badge>
                </div>
                <p className="text-gray-200 mt-0.5 truncate">{log.message}</p>
              </div>
            </button>
          ))}
          {filteredLogs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <Info className="w-8 h-8 mb-2 opacity-50" />
              <p>No logs match your filters</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Detail panel */}
      {selectedLog && (
        <div className="border-t border-dark-700 bg-dark-850 p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-white">Log Details</h4>
            <button
              onClick={() => setSelectedLog(null)}
              className="text-gray-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">ID:</span>
              <span className="text-gray-300 ml-2">{selectedLog.id}</span>
            </div>
            <div>
              <span className="text-gray-500">Timestamp:</span>
              <span className="text-gray-300 ml-2">{formatDate(selectedLog.timestamp)}</span>
            </div>
            <div>
              <span className="text-gray-500">Severity:</span>
              <span className={cn("ml-2 font-medium", getSeverityColor(selectedLog.severity))}>
                {selectedLog.severity}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Source:</span>
              <span className="text-gray-300 ml-2">{selectedLog.source}</span>
            </div>
          </div>
          <div className="mt-2">
            <span className="text-gray-500 text-sm">Message:</span>
            <p className="text-gray-200 text-sm mt-1 font-mono bg-dark-900 p-2 rounded-lg">
              {selectedLog.message}
            </p>
          </div>
          {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
            <div className="mt-2">
              <span className="text-gray-500 text-sm">Metadata:</span>
              <pre className="text-gray-300 text-xs mt-1 font-mono bg-dark-900 p-2 rounded-lg overflow-auto">
                {JSON.stringify(selectedLog.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
