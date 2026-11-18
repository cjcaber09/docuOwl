import { useParams } from "react-router"
import { ChatInput } from "@/components/ChatInput"
import { MessageBubble } from "@/components/MessageBubble"
import { OwlLogo } from "@/components/OwlLogo"
import { ScrollArea } from "@/components/ui/scroll-area"
import { sampleConversations } from "@/data/sampleData"

export function ChatPage() {
  const { conversationId } = useParams()
  const conversation = sampleConversations.find((c) => c.id === conversationId)

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ScrollArea className="min-h-0 flex-1">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 p-4 md:p-8">
          {conversation ? (
            conversation.messages.map((message) => <MessageBubble key={message.id} message={message} />)
          ) : conversationId ? (
            <p className="text-center text-muted-foreground">This conversation doesn't exist.</p>
          ) : (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <OwlLogo className="size-16" />
              <h1 className="text-2xl font-semibold">Ask Owl about your documents</h1>
              <p className="text-muted-foreground">Answers come only from your files, with a citation for every fact.</p>
            </div>
          )}
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput />
        </div>
      </div>
    </div>
  )
}
