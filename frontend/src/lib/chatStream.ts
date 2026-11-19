import { errorFromResponse } from "@/lib/api"
import type { AnswerEvent } from "@/lib/apiTypes"

/** Sends a question and calls onEvent for every line of the streamed answer (one JSON object per line). */
export async function streamAnswer(
  conversationId: string,
  content: string,
  onEvent: (event: AnswerEvent) => void,
): Promise<void> {
  // EventSource can't send a POST with a body, so this is a plain fetch read piece by piece.
  const response = await fetch(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  })
  if (!response.ok) throw await errorFromResponse(response)
  if (!response.body) throw new Error("The answer didn't arrive. Please try again.")

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffered = ""
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffered += decoder.decode(value, { stream: true })
    const lines = buffered.split("\n")
    buffered = lines.pop() ?? "" // the last piece may be the start of an unfinished line
    for (const line of lines) {
      if (line.trim()) onEvent(JSON.parse(line) as AnswerEvent)
    }
  }
  if (buffered.trim()) onEvent(JSON.parse(buffered) as AnswerEvent)
}
