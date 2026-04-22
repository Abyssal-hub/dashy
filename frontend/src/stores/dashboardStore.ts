import { create } from "zustand";
import type { DashboardState } from "@/types";

export const useDashboardStore = create<DashboardState>((set) => ({
  layout: [],
  activeModuleId: null,
  isEditMode: false,
  setLayout: (layout) => set({ layout }),
  setActiveModule: (id) => set({ activeModuleId: id }),
  toggleEditMode: () => set((state) => ({ isEditMode: !state.isEditMode })),
}));
