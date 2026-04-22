export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const GRID_CONFIG = {
  cols: { lg: 4, md: 3, sm: 2, xs: 1 },
  rowHeight: 150,
  breakpoints: { lg: 1200, md: 996, sm: 768, xs: 480 },
  margin: [16, 16] as [number, number],
};

export const MODULE_REFRESH_INTERVAL = 30000; // 30 seconds

export const LOG_STREAM_RETRY_INTERVAL = 5000;
