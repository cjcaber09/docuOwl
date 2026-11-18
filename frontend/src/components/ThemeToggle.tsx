import { Moon, Sun } from "lucide-react"
import { SidebarMenuButton } from "@/components/ui/sidebar"
import { useUiStore } from "@/stores/uiStore"

export function ThemeToggle() {
  const theme = useUiStore((state) => state.theme)
  const toggleTheme = useUiStore((state) => state.toggleTheme)

  return (
    <SidebarMenuButton onClick={toggleTheme}>
      {theme === "dark" ? <Sun /> : <Moon />}
      <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
    </SidebarMenuButton>
  )
}
