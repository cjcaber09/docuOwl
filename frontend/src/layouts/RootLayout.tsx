import { Outlet } from "react-router"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { useApplyTheme } from "@/hooks/useApplyTheme"

export function RootLayout() {
  useApplyTheme()

  return (
    <TooltipProvider>
      <Outlet />
      <Toaster position="top-center" />
    </TooltipProvider>
  )
}
