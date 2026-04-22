import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(value);
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString();
}

export function timeAgo(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "ERROR":
      return "text-status-critical";
    case "WARN":
      return "text-status-warning";
    case "INFO":
      return "text-status-info";
    default:
      return "text-gray-400";
  }
}

export function getSeverityBgColor(severity: string): string {
  switch (severity) {
    case "ERROR":
      return "bg-red-500/10 border-red-500/20";
    case "WARN":
      return "bg-amber-500/10 border-amber-500/20";
    case "INFO":
      return "bg-blue-500/10 border-blue-500/20";
    default:
      return "bg-gray-500/10 border-gray-500/20";
  }
}

export function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadCSV(
  headers: string[],
  rows: (string | number | boolean | null | undefined)[][],
  filename: string
) {
  const csv = [
    headers.join(","),
    ...rows.map((row) =>
      row
        .map((cell) => {
          const val = cell ?? "";
          const str = String(val).replace(/"/g, '""');
          return str.includes(",") || str.includes('"')
            ? `"${str}"`
            : str;
        })
        .join(",")
    ),
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
