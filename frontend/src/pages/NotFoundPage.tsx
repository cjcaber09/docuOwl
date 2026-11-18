import { Link } from "react-router"
import { OwlLogo } from "@/components/OwlLogo"
import { Button } from "@/components/ui/button"

export function NotFoundPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 p-4 text-center">
      <OwlLogo className="size-16" />
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="text-muted-foreground">Owl looked everywhere but couldn't find this page.</p>
      <Button asChild>
        <Link to="/chat">Back to Owl</Link>
      </Button>
    </div>
  )
}
