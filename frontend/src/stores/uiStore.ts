import { create } from "zustand"
import { persist } from "zustand/middleware"

export type Theme = "light" | "dark"

type UiState = {
  theme: Theme
  sidebarOpen: boolean
  toggleTheme: () => void
  setSidebarOpen: (open: boolean) => void
}

const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: prefersDark ? "dark" : "light",
      sidebarOpen: true,
      toggleTheme: () => set((state) => ({ theme: state.theme === "dark" ? "light" : "dark" })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: "owl-ui",
      // Only the theme is remembered between visits.
      partialize: (state) => ({ theme: state.theme }),
    },
  ),
)
