import { create } from "zustand";
import type { UIState } from "@/types";

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  theme: "dark",
  toast: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  showToast: (message, type) => set({ toast: { message, type } }),
  clearToast: () => set({ toast: null }),
}));
