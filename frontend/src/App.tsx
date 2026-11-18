import { OwlLogo } from "@/components/OwlLogo"
import { Button } from "@/components/ui/button"

export default function App() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 bg-background">
      <OwlLogo className="size-24" />
      <h1 className="text-3xl font-semibold text-foreground">Owl</h1>
      <Button>Purple button</Button>
      <span className="rounded-md bg-highlight px-2 py-1 text-highlight-foreground">Amber highlight</span>
    </div>
  )
}
