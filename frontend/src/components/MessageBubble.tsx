import { CitationChip } from "@/components/CitationChip"
import { OwlLogo } from "@/components/OwlLogo"
import type { SampleMessage } from "@/data/sampleData"

export function MessageBubble({ message }: { message: SampleMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl bg-primary px-4 py-2 whitespace-pre-wrap text-primary-foreground">
          {message.content}
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <OwlLogo className="size-8 shrink-0" />
      <div className="flex min-w-0 flex-col gap-2">
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.citations.map((citation) => (
              <CitationChip key={citation.id} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
