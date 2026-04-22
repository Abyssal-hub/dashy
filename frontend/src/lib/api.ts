import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 by refreshing token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshResponse = await axios.post(
          `${API_BASE}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newToken = refreshResponse.data.access_token;
        localStorage.setItem("token", newToken);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return api.request(originalRequest);
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/";
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  return data as { access_token: string; refresh_token: string };
}

export async function logout() {
  await api.post("/auth/logout");
}

export async function getModules() {
  const { data } = await api.get("/api/modules");
  return data as { modules: import("@/types").Module[]; total: number };
}

export async function getModuleData(moduleId: string, size?: string) {
  const { data } = await api.get(`/api/modules/${moduleId}/data`, {
    params: { size },
  });
  return data as import("@/types").ModuleData;
}

export async function updateModuleLayout(
  moduleId: string,
  layout: Partial<{
    position_x: number;
    position_y: number;
    width: number;
    height: number;
    size: string;
  }>
) {
  const { data } = await api.post(`/api/modules/${moduleId}/layout`, layout);
  return data as import("@/types").Module;
}

export async function getDashboardLayout() {
  const { data } = await api.get("/api/dashboard/layout");
  return data as import("@/types").DashboardLayout;
}

export async function updateDashboardLayout(
  layout: Partial<import("@/types").DashboardLayout>
) {
  const { data } = await api.put("/api/dashboard/layout", layout);
  return data as import("@/types").DashboardLayout;
}

export async function getLogs(params?: {
  severity?: string;
  source?: string;
  limit?: number;
  offset?: number;
}) {
  const { data } = await api.get("/api/logs", { params });
  return data as {
    logs: import("@/types").LogEntry[];
    total: number;
    limit: number;
    offset: number;
  };
}

export function getLogStreamUrl(params?: {
  severity?: string;
  source?: string;
}) {
  const searchParams = new URLSearchParams();
  if (params?.severity) searchParams.append("severity", params.severity);
  if (params?.source) searchParams.append("source", params.source);
  return `${API_BASE}/api/logs/stream?${searchParams}`;
}
