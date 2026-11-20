import { CitationChip } from "@/components/CitationChip"
import { OwlLogo } from "@/components/OwlLogo"
import type { ChatMessage } from "@/lib/apiTypes"

type MessageBubbleProps = Pick<ChatMessage, "role" | "content" | "citations">

export function MessageBubble({ role, content, citations }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl bg-primary px-4 py-2 whitespace-pre-wrap text-primary-foreground">
          {content}
        </p>
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      <OwlLogo className="size-8 shrink-0" />
      <div className="flex min-w-0 flex-col gap-2">
        <p className="whitespace-pre-wrap">{content}</p>
        {citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {citations.map((citation, index) => (
              <CitationChip key={`${citation.filename}-${citation.location}-${index}`} citation={citation} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
