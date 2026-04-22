export interface User {
  id: string;
  email: string;
}

export interface Module {
  id: string;
  module_type: string;
  name: string;
  config: Record<string, unknown>;
  size: string;
  position_x: number;
  position_y: number;
  width: number | null;
  height: number | null;
  refresh_interval: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModuleData {
  module_id: string;
  module_type: string;
  size: string;
  data: Record<string, unknown>;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  severity: "INFO" | "WARN" | "ERROR";
  message: string;
  source: string;
  metadata: Record<string, unknown>;
  module_id?: string;
  severity_color?: string;
}

export interface DashboardLayout {
  id: string;
  user_id: string;
  columns: number;
  row_height: number;
  positions: ModulePosition[];
}

export interface ModulePosition {
  module_id: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface GridLayoutItem {
  i: string;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export interface DashboardState {
  layout: GridLayoutItem[];
  activeModuleId: string | null;
  isEditMode: boolean;
  setLayout: (layout: GridLayoutItem[]) => void;
  setActiveModule: (id: string | null) => void;
  toggleEditMode: () => void;
}

export interface UIState {
  sidebarOpen: boolean;
  theme: "dark";
  toast: { message: string; type: "success" | "error" | "info" } | null;
  toggleSidebar: () => void;
  showToast: (message: string, type: "success" | "error" | "info") => void;
  clearToast: () => void;
}
