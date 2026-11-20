import { useParams } from "react-router"
import { ChatInput } from "@/components/ChatInput"
import { MessageBubble } from "@/components/MessageBubble"
import { OwlLogo } from "@/components/OwlLogo"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAskQuestion } from "@/hooks/useAskQuestion"
import { useConversation } from "@/hooks/useConversations"
import { ApiError } from "@/lib/api"
import { useAnswerStore } from "@/stores/answerStore"

function EmptyChat() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <OwlLogo className="size-16" />
      <h1 className="text-2xl font-semibold">Ask Owl about your documents</h1>
      <p className="text-muted-foreground">Answers come only from your files, with a citation for every fact.</p>
    </div>
  )
}

export function ChatPage() {
  const { conversationId } = useParams()
  const conversation = useConversation(conversationId)
  const answer = useAnswerStore((state) => state.answer)
  const ask = useAskQuestion()

  const messages = conversation.data?.messages ?? []
  const current = answer && answer.conversationId === conversationId ? answer : null
  const lastMessage = messages.at(-1)
  // Until the question is saved on the server, show it from the answer being written.
  const showPendingQuestion = !(lastMessage?.role === "user" && lastMessage.content === current?.question)
  const busy = current !== null && current.error === null
  const notFound = conversation.error instanceof ApiError && conversation.error.status === 404
  // A failed refresh keeps the messages already shown; only a first load that fails has nothing to show.
  const loadFailed = conversation.isError && !conversation.data

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ScrollArea className="min-h-0 flex-1">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 p-4 md:p-8">
          {notFound ? (
            <p className="text-center text-muted-foreground">This conversation doesn't exist.</p>
          ) : loadFailed ? (
            <p className="text-center text-destructive">Couldn't load this conversation. {conversation.error?.message}</p>
          ) : conversationId && conversation.isPending && !current ? (
            <p className="text-center text-muted-foreground">Loading the conversation…</p>
          ) : messages.length === 0 && !current ? (
            <EmptyChat />
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble key={message.id} role={message.role} content={message.content} citations={message.citations} />
              ))}
              {current && showPendingQuestion && <MessageBubble role="user" content={current.question} citations={[]} />}
              {current && current.error === null && (
                <MessageBubble role="assistant" content={current.text || "…"} citations={current.citations} />
              )}
              {current?.error && (
                <div role="alert" className="flex flex-col items-start gap-2 rounded-lg border border-destructive/40 p-3 text-sm">
                  <p className="text-destructive">{current.error}</p>
                  <Button variant="outline" size="sm" onClick={() => void ask(current.conversationId, current.question)}>
                    Retry
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput disabled={busy || notFound} onSend={(question) => void ask(conversationId, question)} />
        </div>
      </div>
    </div>
  )
}
