import { useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router"
import { toast } from "sonner"
import { CONVERSATIONS_KEY, conversationKey } from "@/hooks/useConversations"
import { apiFetch } from "@/lib/api"
import type { ConversationSummary } from "@/lib/apiTypes"
import { streamAnswer } from "@/lib/chatStream"
import { useAnswerStore } from "@/stores/answerStore"

const TROUBLE = "Owl is having trouble right now, please try again."

/** Asks a question; a new chat (no conversation yet) gets a conversation first. */
export function useAskQuestion() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  async function refresh(id: string) {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: conversationKey(id) }),
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY }),
    ])
  }

  return async function ask(conversationId: string | undefined, question: string) {
    const store = useAnswerStore.getState()
    let id = conversationId
    try {
      if (!id) {
        id = (await apiFetch<ConversationSummary>("/conversations", { method: "POST" })).id
        navigate(`/chat/${id}`)
      }
      store.start(id, question)
      let failed = false
      await streamAnswer(id, question, (event) => {
        if (event.type === "text") store.addText(event.text)
        else if (event.type === "citation") store.addCitation(event.citation)
        else if (event.type === "error") {
          failed = true
          store.fail(event.message)
        }
      })
      // The saved question and answer now come from the server, so the streaming copy can go.
      await refresh(id)
      if (!failed) store.clear()
    } catch (error) {
      const message = error instanceof Error ? error.message : TROUBLE
      if (id && useAnswerStore.getState().answer) {
        store.fail(message)
        await refresh(id)
      } else {
        toast.error(message)
      }
    }
  }
}
