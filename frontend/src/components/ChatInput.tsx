import { useState, type FormEvent, type KeyboardEvent } from "react"
import { SendHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

export function ChatInput({ onSend, disabled = false }: { onSend: (question: string) => void; disabled?: boolean }) {
  const [question, setQuestion] = useState("")
  const canSend = question.trim().length > 0 && !disabled

  function send(event?: FormEvent) {
    event?.preventDefault()
    if (!canSend) return
    onSend(question.trim())
    setQuestion("")
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter adds a new line.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      send()
    }
  }

  return (
    <form onSubmit={send} className="flex items-end gap-2">
      <Textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about your documents…"
        aria-label="Your question"
        rows={1}
        className="max-h-40 min-h-10 resize-none"
      />
      <Button type="submit" size="icon" disabled={!canSend} aria-label="Send question">
        <SendHorizontal />
      </Button>
    </form>
  )
}
