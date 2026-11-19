import { Loader2 } from "lucide-react"
import type { ReactNode } from "react"
import { Navigate, Outlet } from "react-router"
import { Button } from "@/components/ui/button"
import { useCurrentUser } from "@/hooks/useAuth"

function FullPageStatus({ children }: { children: ReactNode }) {
  return <div className="flex min-h-svh flex-col items-center justify-center gap-3 p-4 text-center">{children}</div>
}

function CannotReachServer({ onRetry }: { onRetry: () => void }) {
  return (
    <FullPageStatus>
      <p className="text-muted-foreground">Owl can't reach its server right now.</p>
      <Button variant="outline" onClick={onRetry}>
        Try again
      </Button>
    </FullPageStatus>
  )
}

/** Shows the page only to logged-in users; everyone else goes to /login. */
export function RequireAuth() {
  const { data: user, isPending, isError, refetch } = useCurrentUser()

  if (isPending) {
    return (
      <FullPageStatus>
        <Loader2 className="size-6 animate-spin text-muted-foreground" aria-label="Loading" />
      </FullPageStatus>
    )
  }
  if (isError) return <CannotReachServer onRetry={() => void refetch()} />
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

/** Login and sign-up pages: logged-in users go straight to the chat. */
export function GuestOnly() {
  const { data: user, isPending, isError, refetch } = useCurrentUser()

  if (isPending) return null
  if (isError) return <CannotReachServer onRetry={() => void refetch()} />
  if (user) return <Navigate to="/chat" replace />
  return <Outlet />
}
