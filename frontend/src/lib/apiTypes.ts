// The shapes the backend sends back. Keep in sync with backend/app/auth/schemas.py and /api/config.

export type User = {
  id: string
  email: string
}

export type AppConfig = {
  storageEnabled: boolean
  emailEnabled: boolean
}

export type DocumentStatus = "processing" | "ready" | "failed"

// Named OwlDocument so it never gets mixed up with the browser's built-in `Document`.
export type OwlDocument = {
  id: string
  filename: string
  fileType: string
  status: DocumentStatus
  failureReason: string | null
  pageCount: number | null
  createdAt: string
}

export type Citation = {
  filename: string
  location: string
  quote: string
  deleted: boolean
}

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  citations: Citation[]
  createdAt: string
}

export type ConversationSummary = {
  id: string
  title: string
  updatedAt: string
}

export type Conversation = {
  id: string
  title: string
  messages: ChatMessage[]
}

// One line of a streamed answer.
export type AnswerEvent =
  | { type: "text"; text: string }
  | { type: "citation"; citation: Citation }
  | { type: "done"; message: ChatMessage | null; title: string | null }
  | { type: "error"; message: string }
