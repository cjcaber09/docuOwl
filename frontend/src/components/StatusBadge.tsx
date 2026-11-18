import type { ComponentProps } from "react"
import { Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { DocumentStatus } from "@/data/sampleData"

type BadgeVariant = ComponentProps<typeof Badge>["variant"]

const statusDisplay: Record<DocumentStatus, { label: string; variant: BadgeVariant }> = {
  processing: { label: "Processing", variant: "secondary" },
  ready: { label: "Ready", variant: "default" },
  failed: { label: "Failed", variant: "destructive" },
}

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const { label, variant } = statusDisplay[status]

  return (
    <Badge variant={variant}>
      {status === "processing" && <Loader2 className="animate-spin" />}
      {label}
    </Badge>
  )
}
