import { FileText } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import type { Citation } from "@/lib/apiTypes"
import { citationLabel } from "@/lib/format"

export function CitationChip({ citation }: { citation: Citation }) {
  const label = citationLabel(citation)

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex max-w-full items-center gap-1 rounded-full border bg-highlight/15 px-2.5 py-0.5 text-xs font-medium hover:bg-highlight/30"
        >
          <FileText className="size-3 shrink-0" />
          <span className="truncate">{label}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <p className="text-sm font-medium">{label}</p>
        <blockquote className="mt-2 border-l-2 border-highlight pl-3 text-sm text-muted-foreground italic">
          "{citation.quote}"
        </blockquote>
      </PopoverContent>
    </Popover>
  )
}
