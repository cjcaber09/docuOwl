import { Outlet } from "react-router"
import { OwlLogo } from "@/components/OwlLogo"

export function AuthLayout() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted/40 p-4">
      <div className="flex items-center gap-2">
        <OwlLogo className="size-12" />
        <span className="text-2xl font-semibold">Owl</span>
      </div>
      <div className="w-full max-w-sm">
        <Outlet />
      </div>
    </div>
  )
}
